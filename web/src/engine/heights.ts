/** Height grid in local metres (x east, y north); bilinear sampling. */
export interface HeightData { x0: number; y0: number; step: number; w: number; h: number; z?: number[]; zb64?: string }

export class Heights {
  private z: ArrayLike<number>;

  constructor(private d: HeightData) {
    if (d.zb64) { // int16 centimetres, little endian
      const b = Uint8Array.from(atob(d.zb64), (c) => c.charCodeAt(0));
      const cm = new Int16Array(b.buffer);
      this.z = Float32Array.from(cm, (v) => v / 100);
    } else this.z = d.z ?? [];
  }

  /** Terrain height at local (x, y). */
  at(x: number, y: number): number {
    const { x0, y0, step, w, h } = this.d, z = this.z;
    const fx = Math.min(Math.max((x - x0) / step, 0), w - 1.001);
    const fy = Math.min(Math.max((y - y0) / step, 0), h - 1.001);
    const ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
    const i = iy * w + ix;
    return z[i] * (1 - tx) * (1 - ty) + z[i + 1] * tx * (1 - ty) + z[i + w] * (1 - tx) * ty + z[i + w + 1] * tx * ty;
  }
}
