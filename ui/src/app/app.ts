import { Component, ElementRef, ViewChild, signal, computed, OnInit, OnDestroy } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
type Segment = [number, number, string];
type ControlEvidence = { candidate: string | null; motionSpeed: number | null; deadCue: string | null; restartContext: boolean; restartMotion: boolean };
type Row = { control: ControlEvidence; players: { x: number; y: number; team: number; slot: number }[]; ball: number[] | null; nearest: (number | null)[] };
type Phase = { code: string; start_frame: number; end_frame: number; tags: Record<string, string> };
type Model = { segments: Segment[]; counts: Record<string, number>; sha256: string };
type Summary = { frames: number; fps: number; ballPresent: number; trackSlots: number; models: Record<string, Model>; events: Phase[] };
@Component({ selector: 'app-root', imports: [FormsModule, DecimalPipe], templateUrl: './app.html', styleUrl: './app.css' })
export class App implements OnInit, OnDestroy {
  @ViewChild('video') video?: ElementRef<HTMLVideoElement>;
  summary = signal<Summary | null>(null);
  frame = signal(11185);
  readonly model = 'experimental_control_v5';
  window = signal<{start: number; end: number; rows: Row[]} | null>(null);
  error = signal('');
  loading = signal(false);
  playing = signal(false);
  frameInput = 11185;
  speed = 1;
  private controller?: AbortController;
  private requestedFrame = -1;
  private clock = 0;
  row = computed(() => { const w = this.window(); return w && this.frame() >= w.start && this.frame() < w.end ? w.rows[this.frame()-w.start] : null; });
  currentModel = computed(() => this.summary()?.models[this.model]);
  segments = computed(() => this.currentModel()?.segments ?? []);
  current = computed(() => this.segments().find(s => s[0] <= this.frame() && this.frame() < s[1]));
  label = computed(() => this.current()?.[2] ?? 'X');
  async ngOnInit() {
    try {
      const res = await fetch('/api/summary');
      if (!res.ok) throw new Error('Cannot load match summary. Run lab/build.py first.');
      this.summary.set(await res.json());
      if (!this.currentModel()) throw new Error('Control v5 is unavailable. Run npm run rebuild-data.');
      await this.loadWindow(this.frame());
    } catch (err) { this.error.set(String(err)); }
    this.clock = window.setInterval(() => {
      const v = this.video?.nativeElement;
      if (v && !v.paused) this.updateFrame(Math.round(v.currentTime*25));
    }, 40);
  }
  ngOnDestroy() { clearInterval(this.clock); this.controller?.abort(); }
  async loadWindow(frame: number) {
    this.controller?.abort();
    const controller = new AbortController();
    this.controller = controller;
    this.requestedFrame = frame;
    this.loading.set(true);
    try {
      const res = await fetch(`/api/window?frame=${frame}`, { signal: controller.signal });
      if (!res.ok) throw new Error('Tracking data could not be loaded.');
      this.window.set(await res.json());
      this.error.set('');
    } catch (err) { if (!controller.signal.aborted) this.error.set(String(err)); }
    finally { if (this.controller === controller) { this.loading.set(false); this.requestedFrame = -1; } }
  }
  updateFrame(f: number) {
    const frame = Math.max(0, Math.min((this.summary()?.frames ?? 199319)-1, f));
    this.frame.set(frame); this.frameInput = frame;
    const w = this.window();
    const needsWindow = !w || frame < w.start || frame >= w.end || (w.end < (this.summary()?.frames ?? 199319) && frame >= w.end-50);
    if (needsWindow && (this.requestedFrame < 0 || Math.abs(frame-this.requestedFrame)>375)) void this.loadWindow(frame);
  }
  seek(frame: number) { if (!Number.isFinite(frame)) return; this.updateFrame(Math.round(frame)); if (this.video) this.video.nativeElement.currentTime = this.frame()/25; }
  videoReady() { this.seek(this.frame()); }
  videoTime() { const v = this.video?.nativeElement; if (v) this.updateFrame(Math.round(v.currentTime*25)); }
  async togglePlay() { const v = this.video?.nativeElement; if (!v) return; try { v.paused ? await v.play() : v.pause(); } catch { this.error.set('Video playback failed. Check the local path and browser codec support.'); } }
  async toggleFullscreen(player: HTMLElement) {
    try { document.fullscreenElement ? await document.exitFullscreen() : await player.requestFullscreen(); }
    catch { this.error.set('Fullscreen is unavailable in this browser.'); }
  }
  changeSpeed() { if (this.video) this.video.nativeElement.playbackRate = Number(this.speed); }
  time(frame: number) { const sec = Math.floor(frame/25); return `${Math.floor(sec/3600).toString().padStart(2,'0')}:${Math.floor(sec/60%60).toString().padStart(2,'0')}:${(sec%60).toString().padStart(2,'0')}`; }
  name(label: string) { return ({H:'Barcelona', A:'Athletic Club', D:'Dead ball', X:'No answer'} as Record<string,string>)[label] ?? label; }
  exportUrl() { return '/api/export?model='+this.model; }
}
