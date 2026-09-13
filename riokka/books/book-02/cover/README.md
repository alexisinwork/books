# Обложка книги 2 «Прочие убытки»

Статус: второй концепт для авторского просмотра. Эталон серии — `books/book-01/cover/cover-concept-v2-calm.png`; правила — `riokka/COVER-STYLE.md`.

Текущий файл: [cover-concept-v2-ledger.png](cover-concept-v2-ledger.png), 1024 × 1536, RGB PNG. SHA-256 `8a5bc5acf9e450467907c0d09efb9d7247722f3a04ca1968b957462a69d42231`.

Первый панорамный вариант сохранён как [cover-concept-v1.png](cover-concept-v1.png), SHA-256 `4f33e8915bab6a8aa2502f7a6ea445cc36ca90870459ad73014b863603a7d416`.

## Новый концепт

Композиция перенесена внутрь «Последней мили». Кай показан в три четверти за рабочим столом: он вручную считает пассажирские жетоны рядом с книгой пустых строк. Велд, кольцо буёв и шесть уходящих кораблей видны через круглый иллюминатор и остаются вторым планом. Единственный насыщенный акцент — тонкая зелёная нить слухача, сгорающая на столе.

От первой обложки сохранены живописный реализм, холодная сталь с тёплым светом, человек в центре нравственного выбора и трёхуровневая типографика. Не повторяются человек спиной, открытая рампа, мост с беженцами и контейнер в правом нижнем углу.

Текст обложки:

- `КОНТРАКТНИК`
- `КНИГА 2`
- `ПРОЧИЕ УБЫТКИ`

Другого текста, имени автора, логотипов и водяных знаков нет.

## Финальный промпт второго концепта

```text
Use case: stylized-concept
Asset type: radically new front-cover concept for Book 2 in an established Russian science-fiction series, portrait 2:3.
Input image: the supplied Book 1 cover is a REFERENCE ONLY for series-level painterly realism, restrained palette, large condensed Cyrillic typography, and calm three-level hierarchy. Do not reuse its scene, viewpoint, silhouette, ramp, catwalk, foreground crate, or landscape composition.

Primary request: create a clearly distinct visual concept for Book 2, intimate and psychological rather than panoramic.

Scene/backdrop: the dim interior of a rugged courier ship. A large circular observation window dominates the upper middle background. Through the window we see only a restrained glimpse of the rust-red quarry world Vel'd, its thin orbital beacon ring, and six small departing ships separated across space. No sprawling city panorama.

Subject: one practical, tired male rescuer, Kai, shown in three-quarter side profile at a scarred metal table, face partly visible and human, not glamorous. He is seated or leaning over the table, counting worn passenger tags beside an open handmade ledger filled with rows and blank spaces. His posture carries responsibility and fatigue. No weapon, no heroic stance, no person viewed from behind at an open ramp.

Narrative accent: a single thin pale-green living root fiber lies across the dark tabletop beside the ledger, one end beginning to char. It casts a subtle green reflection across Kai's fingers and one blank page. No glass specimen crate, no glowing box, no plant in the lower-right corner.

Composition: bold, calm, graphic cover. Tight interior framing, person and ledger as the main middle-level focus, circular window as a simple secondary shape. Large clean dark cloud/metal area behind the top title and a clean dark lower band behind the book title. Strong thumbnail readability, low visual noise, large tonal masses, atmospheric painterly realism. The visual metaphor is the human cost hidden behind correct numbers.

Lighting/mood: cold graphite-blue ship interior, muted rust light from Vel'd through the round window, one restrained pale-green reflection. Quiet tension, moral accounting, exhaustion after rescue.

Text, exact verbatim Cyrillic:
Top, very large narrow condensed sans serif, distressed white, same typographic family and scale as the reference: "КОНТРАКТНИК"
Below it, small widely tracked white text between thin horizontal rules: "КНИГА 2"
Bottom, very large narrow condensed sans serif, pale white: "ПРОЧИЕ УБЫТКИ"

Constraints: exact Cyrillic spelling; all three text lines fully visible, centered, and highly legible at thumbnail size. No author name. No other readable text, letters, numbers, signage, logos, publisher marks, or watermark. Do not place the person against an open cargo ramp. Do not show a line of evacuees on a bridge. Do not repeat the Book 1 or prior Book 2 composition.
```

Создано встроенным инструментом `image_gen` с выбранной обложкой книги 1 как стилевой ссылкой.
