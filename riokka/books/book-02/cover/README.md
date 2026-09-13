# Обложка книги 2 «Прочие убытки»

Статус: созданный концепт для авторского просмотра. Эталон серии — `books/book-01/cover/cover-concept-v2-calm.png`; правила — `riokka/COVER-STYLE.md`.

Файл: [cover-concept-v1.png](cover-concept-v1.png), 1024 × 1536, RGB PNG. SHA-256 `4f33e8915bab6a8aa2502f7a6ea445cc36ca90870459ad73014b863603a7d416`.

## Визуальное решение

Велд показан как ржавый промышленный карьерный мир под кольцом буёв. Кай стоит у рампы «Последней мили» и смотрит на несколько потоков эвакуации; в среднем плане видны пять транспортов, образующие вместе с его кораблём шесть маршрутов. Единственный насыщенный акцент — зелёный слухач в техническом контейнере.

Текст обложки:

- `КОНТРАКТНИК`
- `КНИГА 2`
- `ПРОЧИЕ УБЫТКИ`

Другого текста, имени автора, логотипов и водяных знаков нет.

## Финальный промпт

```text
Use case: stylized-concept
Asset type: front cover for the second novel in an established Russian science-fiction series, portrait 2:3.
Input image: the supplied Book 1 cover is a STYLE AND SERIES-LAYOUT REFERENCE ONLY. Preserve its calm visual discipline, painterly cinematic realism, three-level hierarchy, typography character, restrained detail, and thumbnail readability. Do not copy its scene literally.
Primary request: create the matching cover for Book 2 of the same series.
Scene/backdrop: the rust-colored industrial quarry world Vel'd at dusk, a vast terraced mine and blockaded settlement beneath a sparse ring of orbital beacons; five utilitarian transport ships and one rugged courier ship form six distinct evacuation routes in the middle distance. Simplify secondary architecture into large atmospheric masses.
Subject: Kai seen from behind in practical worn work clothes, standing at the open cargo ramp of the courier ship and looking down toward orderly lines of evacuees moving along several separate gangways. Human and vulnerable, no heroic pose, no weapon pointed at the viewer.
Narrative object/accent: in the lower right foreground, one compact transparent technical containment module holding a pale-green living listener-root with delicate glowing fibers; it is strained and beginning to darken at the edges. This is the only saturated color accent.
Lighting/mood: cold graphite and steel shadows, rust and muted amber industrial light, solemn urgency, responsibility, calculated rescue, atmospheric depth, low visual noise.
Composition: mirror the reference cover's clean three-level hierarchy without duplicating its layout pixel-for-pixel. Large negative space and dark clouds behind the title; central silhouette and evacuation movement; dark lower band behind the book title. Crisp focal elements, softer distant planes.
Text, exact verbatim Cyrillic:
Top, very large narrow condensed sans serif, white: "КОНТРАКТНИК"
Below it, small widely tracked white text between thin horizontal rules: "КНИГА 2"
Bottom, very large narrow condensed sans serif, pale white: "ПРОЧИЕ УБЫТКИ"
Constraints: exact Cyrillic spelling; all three text lines fully visible, centered, and highly legible at thumbnail size; no author name; no other text, letters, numbers, signs, logos, publisher marks, or watermark. Premium contemporary cinematic science-fiction cover, painterly realism, calm composition, low visual noise, believable industrial technology.
```

Создано встроенным инструментом `image_gen` с выбранной обложкой книги 1 как стилевой ссылкой.
