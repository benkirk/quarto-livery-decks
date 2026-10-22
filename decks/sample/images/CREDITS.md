# Image credits

The sample deck's gallery images (`gallery-1.jpg` ... `gallery-6.jpg`, also the LaTeX cookbook's
through `latex/images/`) are NASA photographs from the NASA Image and Video Library
(images.nasa.gov), each its `~large` file downscaled to 960 px on its long side. NASA content is
generally not subject to copyright in the United States, and NASA is acknowledged as the source
([NASA's media usage guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/)). The
NASA insignia and logotype on the Artemis I rocket stay protected; the photos are used here as
they are, with no endorsement implied.

| File | Image | NASA ID | Date | Credit |
|---|---|---|---|---|
| `gallery-1.jpg` | The Blue Marble: Earth from Apollo 17 on the way to the Moon | [as17-148-22727](https://images.nasa.gov/details/as17-148-22727) | 1972-12-07 | NASA (JSC) |
| `gallery-2.jpg` | Earthrise: Earth over the lunar horizon from Apollo 8 | [as08-14-2383](https://images.nasa.gov/details/as08-14-2383) | 1968-12-24 | NASA (JSC) |
| `gallery-3.jpg` | Artemis I launch, the Space Launch System and Orion | [NHQ202211160003](https://images.nasa.gov/details/NHQ202211160003) | 2022-11-16 | NASA/Joel Kowsky |
| `gallery-4.jpg` | An aurora over the Earth's limb, from the International Space Station | [iss058e005282](https://images.nasa.gov/details/iss058e005282) | 2019-01-18 | NASA (JSC) |
| `gallery-5.jpg` | Hurricane Helene, from the International Space Station | [iss072e001649](https://images.nasa.gov/details/iss072e001649) | 2024-09-25 | NASA (JSC) |
| `gallery-6.jpg` | Artemis I launch, a wide view of the pad | [NHQ202211160005](https://images.nasa.gov/details/NHQ202211160005) | 2022-11-16 | NASA/Joel Kowsky |

Their shapes are chosen for the gallery slides: two square (1 and 2), one tall (3, 0.61:1) and three
wide (4 at 3:2, 5 at 16:9, 6 at 2.5:1), so `fit=contain` letterboxes some both ways and `fit=cover`
crops them.
