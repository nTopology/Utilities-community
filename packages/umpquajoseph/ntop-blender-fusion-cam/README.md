# nTop → Blender → Fusion: Lightweight Mesh Export & CAM

Decimate dense nTop meshes in Blender to reduce file size by up to 10x without sacrificing fidelity, then take the reduced model all the way through to CNC manufacturing in Fusion 360.

The core problem this solves: when you directly use the mesh result from implicit modeling without post-processing, high-density nTop models (lattices, scaffolds, voronoi structures) produce very large mesh files, which is entirely natural given the geometric complexity of these structures. Trying to share, demo, or machine these without decimation leads to extreme load times and frequent crashes in downstream tools. Blender's decimation modifier provides a flexible option for this step in the workflow.

## Workflow

### Part 1 - Lighten the mesh in Blender

[Watch the tutorial (Video 1)](https://youtu.be/r7uYutD8P2g)

Export your mesh from nTop, then use Blender's Decimate modifier to shrink the file size while staying within fidelity tolerance. In the example, a 1 GB+ scaffold model comes down to ~2 MB with no meaningful visual loss.

As a bonus, Blender also lets you colorize models and export them as colored 3D files, useful for sharing and demos.

### Part 2 - Machine the mesh in Fusion 360

[Watch the tutorial (Video 2)](https://www.youtube.com/watch?v=_EKJIaY0cqs)

Take the decimated mesh into Fusion 360 for CAM. Two important differences when machining mesh bodies vs. CAD bodies:

- You cannot reference individual faces, edges, or points; only the mesh as a whole.
- The toolpaths that work best for meshes are **3D Flat** and **3D Scallop**.

The example part was machined with a roughing bit only (limited CNC time). Fidelity improves significantly with smaller bit sizes or a dedicated finishing pass.

## Example files

| File | Description | Tutorial |
|------|-------------|---------|
| `high-density-scaffold.ntop` | High-density scaffold, Blender decimation example | [Video 1](https://youtu.be/r7uYutD8P2g) |
| `voronoi-gradient.ntop` | Voronoi gradient, source model for manufacturing | [Video 2](https://www.youtube.com/watch?v=_EKJIaY0cqs) |
| `fusion-manufactured-voronoi-gradient.f3d` | Fusion 360 file with CAM toolpaths set up | [Video 2](https://www.youtube.com/watch?v=_EKJIaY0cqs) |
| `manufactured-full-scale.jpeg` | Photo of the CNC-machined voronoi part | |
| `manufactured-close-up.jpeg` | Close-up of the machined surface | |

## License

MIT.
