# HUMAN-LIKE MANGA / MANHWA STORY PRODUCTION SYSTEM
## الإصدار 1.0 — نظام بشري للحفاظ على الاستمرارية البصرية والمنطقية والسردية

> محفوظ حرفياً كما ورد من المستخدم (2026-09-15). التنفيذ البرمجي: `vtsys/canon.py` (§5.0).

---

## 0. الهدف العام

هذا المستند يعرّف نظامًا إنتاجيًا متكاملًا لإنشاء قصص **Manga / Manhwa** طويلة أو قصيرة باستخدام وكيل ذكاء اصطناعي، مع التركيز على المشكلة الأصعب في هذا النوع من المشاريع:

> **كيف نجعل القصة تبدو وكأن فريقًا بشريًا محترفًا أنشأها، بحيث تبقى الشخصيات والأغراض والأماكن والملابس والطقس والإضاءة والزمن والأحداث مترابطة ومنطقية عبر جميع الصفحات والمشاهد؟**

النظام لا يتعامل مع كل صورة أو صفحة كعمل منفصل، بل يعامل المشروع كـ **عالم مستمر له حالة State** تتغير مع الزمن.

الوكيل يجب ألا يسأل فقط:
- ماذا يجب أن يظهر في الصورة؟

بل يجب أن يسأل دائمًا:
- أين نحن؟
- متى نحن؟
- ماذا حدث قبل هذه اللحظة؟
- من الموجود؟
- ماذا يحمل كل شخص؟
- ماذا كان يرتدي؟
- هل تغيرت حالته الجسدية؟
- ما مصدر الضوء؟
- هل الوقت ليل أم نهار؟
- ما الفصل؟
- ما حالة الطقس؟
- هل المكان داخلي أم خارجي؟
- ما الأشياء التي كانت موجودة في المشهد السابق؟
- ماذا يجب أن يبقى؟
- ماذا يجب أن يتغير؟
- هل التغيير له سبب منطقي؟
- هل هذا الشيء يمكن أن يكون هنا أصلًا؟
- هل المسافة والموقع والحركة منطقية؟
- هل الإصابات/الأوساخ/البلل/الدم/التعب/تلف الملابس استمرت بشكل صحيح؟
- هل الشخصية ما زالت تحمل الغرض نفسه؟
- هل ترتيب الأثاث والمداخل والنوافذ والمركبات والأشياء ثابت؟

---

# 1. المبدأ الأساسي

## 1.1 المشهد ليس صورة مستقلة

كل Panel / Page / Scene هو:

`WORLD STATE(t) + EVENT(t) + CAMERA + ART DIRECTION`

وليس:

`Prompt -> Image`

يجب بناء كل مشهد من الحالة الحالية للعالم.

---

# 2. بنية النظام العامة

النظام يتكون من 12 طبقة رئيسية:

1. **Story Bible**
2. **World Bible**
3. **Character Bible**
4. **Location Bible**
5. **Object / Prop Bible**
6. **Timeline & Event State**
7. **Continuity Engine**
8. **Environment & Weather Engine**
9. **Scene Planner**
10. **Panel / Page Composer**
11. **Visual Prompt Compiler**
12. **Quality Control & Continuity Validator**

التدفق الإجباري:

```text
IDEA
  ↓
STORY BIBLE
  ↓
WORLD BIBLE
  ↓
CHARACTER / LOCATION / PROP DATABASE
  ↓
TIMELINE
  ↓
CURRENT WORLD STATE
  ↓
SCENE PLAN
  ↓
CONTINUITY CHECK
  ↓
PANEL PLAN
  ↓
IMAGE PROMPTS
  ↓
GENERATION
  ↓
VISUAL QC
  ↓
CONTINUITY UPDATE
  ↓
NEXT SCENE
```

---

# 3. قاعدة ذهبية: Canon First

يجب وجود مصدر واحد للحقيقة:

## CANON

كل معلومة ثابتة أو مؤكدة تدخل في قاعدة Canon.

مثال:

```yaml
character:
  id: CH_001
  name: "Kaito"
  age: 21
  height_cm: 181
  hair:
    color: black
    style: medium_wavy
    canonical: true
  eyes:
    color: dark_brown
  scar:
    location: left_eyebrow
    permanent: true
```

لا يجوز للوكيل ابتكار نسخة جديدة من الشخصية في كل Prompt.

---

# 4. أنواع المعلومات

كل معلومة يجب تصنيفها إلى:

### A. FIXED
ثابتة ولا تتغير إلا بحدث صريح.

مثال:
- لون العين
- شكل الندبة
- طول الشخصية
- تصميم المنزل
- شكل السيارة
- لون السيف

### B. STATEFUL
تتغير مع الزمن.

مثال:
- الملابس
- الإصابة
- الدم
- التعب
- المال
- الأدوات المحمولة
- تسريحة الشعر
- البطارية
- الوقود

### C. CONTEXTUAL
تُحدد حسب السياق.

مثال:
- الإضاءة
- الطقس
- الظلال
- زحام المكان
- تعبير الوجه
- وضعية الجسم

### D. TEMPORARY
تظهر لفترة ثم تختفي.

مثال:
- كوب القهوة
- مظلة
- هاتف في يد الشخصية
- جرح حديث
- دخان
- مطر
- سيارة مستأجرة

---

# 5. معرفات ثابتة IDs

كل عنصر مهم يجب أن يملك ID.

مثال:

```text
CH-001 = Kaito
CH-002 = Hana

LOC-001 = Apartment
LOC-002 = School
LOC-003 = Alley

PROP-001 = Black Smartphone
PROP-002 = Silver Key
PROP-003 = Red Umbrella

OUT-001 = Black Jacket
OUT-002 = School Uniform
```

هذا مهم جدًا لأن الاسم وحده قد يسبب اختلافًا.

---

# 6. Character Bible

كل شخصية يجب أن يكون لها ملف شامل.

## الحد الأدنى:

```yaml
id:
name:
age:
sex:
height:
body_type:
face_shape:
jaw:
nose:
eyes:
eyebrows:
hair:
skin:
distinguishing_marks:
voice:
personality:
default_expression:
typical_posture:
walking_style:
handedness:
dominant_side:
clothing:
accessories:
injuries:
relationships:
current_state:
```

---

# 7. Visual Identity Lock

لكل شخصية يجب استخراج:

### الوجه
- Face shape
- Jaw shape
- Eye spacing
- Eye shape
- Eyebrow geometry
- Nose structure
- Mouth proportions
- Ear structure

### الشعر
- اللون
- الطول
- الكثافة
- اتجاه الخصل
- فرق الشعر
- شكل الأطراف

### الجسم
- الطول النسبي
- عرض الكتفين
- طول الذراعين
- طول الساقين
- نسبة الرأس للجسم
- بنية الجسم

### العلامات المميزة
- ندبة
- شامة
- وشم
- نظارة
- حلق
- ساعة
- رباط

### قاعدة:

> الشخصية نفسها يجب أن تكون قابلة للتعرف عليها حتى لو تغيرت:
> الملابس + الوضعية + التعبير + زاوية الكاميرا + الإضاءة.

---

# 8. Character State Tracker

الشخصية لها حالة متغيرة:

```yaml
current_state:
  location: LOC-002
  room: R-03
  time: 2026-01-14 18:42
  clothing_set: OUT-002
  shoes: SHOE-001
  accessories:
    - PROP-002
  held_objects:
    right_hand: PROP-005
    left_hand: none
  injuries:
    left_arm:
      severity: 2
  fatigue: medium
  wetness: 0.4
  dirt_level: 0.2
  emotional_state: anxious
  hairstyle_state: normal
```

أي صورة جديدة يجب أن تُبنى على هذا الـ state.

---

# 9. Clothing Continuity

الملابس لا تعود إلى حالتها الأصلية تلقائيًا.

مثال:

```text
08:00
Clean white shirt

09:20
Minor dirt

11:40
Wrinkled

14:00
Rain exposure

14:30
Wet shirt + darker fabric

15:20
Dried partially

18:00
Still wrinkled
```

لا يجوز الانتقال من:

`Wet -> perfectly dry`

من دون مرور زمني أو سبب.

---

# 10. Damage / Injury Continuity

الإصابة تتطور منطقيًا.

مثال:

```text
Scene 12:
Fresh cut

Scene 13:
Blood present

Scene 14:
Bandage applied

Scene 20:
Bandage remains unless removed

Scene 25:
Healing state
```

لا يجوز اختفاء الإصابة فجأة.

---

# 11. Prop Continuity

الأغراض يجب تتبعها مثل الشخصيات.

مثال الهاتف:

```yaml
PROP-001:
  owner: CH-001
  location:
    current: LOC-002
  condition: normal
  battery: 73
  color: black
  held_by: right_hand
```

إذا وضع الهاتف على الطاولة:

```text
held_by = none
surface = desk_01
```

إذا خرجت الشخصية:

> يجب ألا يظهر الهاتف في يدها إلا إذا أخذته مجددًا.

---

# 12. Object Ownership

لكل غرض:

```text
owner
current_location
current_holder
condition
quantity
state
last_seen
```

مثال:

```yaml
PROP-003:
  name: House Key
  owner: CH-001
  current_holder: CH-001
  current_location: LOC-001
  pocket: right_pocket
```

---

# 13. Location Bible

كل مكان يجب أن يكون قاعدة بيانات، وليس مجرد اسم.

لكل Location:

```yaml
id:
name:
type:
country:
city:
district:
architecture:
floor:
rooms:
doors:
windows:
stairs:
furniture:
fixed_objects:
entrances:
exits:
orientation:
lighting_sources:
materials:
colors:
damage:
weather_exposure:
```

---

# 14. Spatial Memory

كل مكان مهم يجب أن يمتلك خريطة منطقية.

مثال:

```text
Apartment
 ├── Entrance
 ├── Living Room
 │    ├── Sofa
 │    ├── TV
 │    └── Window
 ├── Kitchen
 ├── Bathroom
 └── Bedroom
```

يجب ألا ينتقل الباب أو النافذة أو الأثاث عشوائيًا.

---

# 15. Spatial Coordinate System

يمكن استخدام إحداثيات تقريبية:

```text
Room Coordinate System

(0,0) = reference corner

Door = (0.8, 3.2)
Window = (4.1, 0.3)
Desk = (2.5, 1.4)
Bed = (4.0, 3.5)
```

لا تحتاج الصورة إلى إظهار الإحداثيات، لكنها تستخدم داخليًا لمنع التناقض.

---

# 16. Scene Geography

عند الانتقال بين الأماكن:

```text
HOUSE
 ↓ 8 min walk
STREET
 ↓ 12 min bus
SCHOOL
```

لا يجوز الانتقال مباشرة من المنزل إلى المدرسة ثم الرجوع ثم ظهور المطر دون تفسير زمني أو مكاني.

---

# 17. Time Engine

يجب تتبع الوقت بالدقيقة عندما يكون ذلك مهمًا.

مثال:

```text
09:10
09:18
09:35
10:05
```

ويمكن استخدام نطاق تقريبي عندما لا تكون الدقة مهمة:

```text
Morning
Late Morning
Afternoon
Evening
Night
Late Night
```

لكن عند الحاجة إلى الاستمرارية، يُستخدم الوقت الدقيق.

---

# 18. Day / Night Logic

الإضاءة يجب أن تتوافق مع:

- وقت اليوم
- الموقع الجغرافي
- اتجاه النوافذ
- الطقس
- مصدر الإضاءة

مثال:

### Night
لا تستخدم ضوء شمس مباشر.

### Sunset
يجب وجود انتقال تدريجي.

### Indoor Night
المشهد يمكن أن يحتوي:
- مصباح سقف
- شاشة
- ضوء شارع
- مصباح مكتب

---

# 19. Season Engine

النظام يجب أن يعرف:

```text
Spring
Summer
Autumn
Winter
```

والفصل يؤثر على:

- الملابس
- النباتات
- طول النهار
- المطر
- الثلج
- الضباب
- درجة الحرارة
- ألوان البيئة
- كثافة الجمهور

لا يجوز ظهور:
- معطف شتوي ثقيل في حر الصيف
- أشجار مزهرة في فصل غير منطقي
- ثلج في منطقة لا يوجد فيها ضمن سيناريو العالم
دون تفسير.

---

# 20. Weather Engine

الطقس حالة مستمرة، وليس مؤثرًا بصريًا عشوائيًا.

```yaml
weather:
  type: rain
  intensity: medium
  temperature_c: 11
  humidity: 91
  wind: moderate
  visibility: reduced
```

ويؤثر على:

### الشخصيات
- الملابس المبتلة
- الشعر
- البشرة
- ردود الفعل
- المظلات

### البيئة
- الأرض
- الانعكاسات
- برك الماء
- الضباب
- السيارات
- النوافذ

### الإضاءة
- سماء غائمة
- ضوء منتشر
- انعكاسات رطبة

---

# 21. Weather Continuity

مثال:

```text
17:00 Light rain
17:30 Heavy rain
18:10 Rain stops
18:20 Wet streets
18:50 Drying
```

لا يجوز أن تصبح الأرض جافة بعد دقيقتين دون سبب منطقي.

---

# 22. Climate / Geographic Logic

الموقع الجغرافي يغير قواعد العالم.

يجب مراعاة:

- المناخ
- التضاريس
- الهندسة المعمارية
- النباتات
- الملابس
- نمط المعيشة
- المواد
- اتجاه الشمس
- طول النهار
- الطقس المحتمل

المبدأ:

> لا تخترع المناخ من أجل الصورة؛ اجعل الصورة ناتجة عن العالم.

---

# 23. Indoor / Outdoor Continuity

عند الانتقال:

```text
OUTDOOR
→ DOOR
→ ENTRY
→ ROOM
```

يجب تحديث:

- درجة الحرارة
- البلل
- الضوضاء
- الإضاءة
- الملابس
- الأحذية
- آثار المطر
- الحالة العاطفية

مثال:

إذا كانت الشخصية مبتلة خارجًا ثم دخلت المنزل:

```text
wet coat = remains
wet shoes = remains
hair moisture = remains
floor near entrance = may become wet
```

---

# 24. Lighting Continuity

لكل Scene:

```yaml
lighting:
  time:
  source:
  direction:
  intensity:
  color_temperature:
  shadows:
  atmosphere:
```

مصادر الضوء المحتملة:

- Sun
- Moon
- Window
- Ceiling lamp
- Street lamp
- Neon sign
- Vehicle
- Screen
- Fire
- Candle

---

# 25. Camera Continuity

ليس مطلوبًا أن تكون الكاميرا ثابتة دائمًا، لكن يجب احترام الجغرافيا.

يجب تتبع:

- اتجاه الشخصية
- يمين / يسار
- Front / Back
- Screen direction
- Eye line
- 180-degree rule عند الحاجة
- محور الحركة

---

# 26. Screen Direction

مثال:

المشهد السابق:

```text
Character A → يمين
Character B → يسار
```

المشهد التالي يجب ألا يعكس الاتجاه بلا سبب أو انتقال كاميرا واضح.

---

# 27. Action Continuity

الحركة يجب أن تتبع:

```text
State Before
→ Action
→ State After
```

مثال:

```text
Door closed
→ character opens door
→ door open
```

وليس:

```text
door closed
→ next panel door open
→ next panel closed
```

بدون تفسير.

---

# 28. Cause-and-Effect Engine

كل تغيير مهم يجب أن يكون له:

```text
CAUSE
→ EVENT
→ RESULT
```

أمثلة:

```text
Rain
→ walks outside
→ clothes become wet
```

```text
Fight
→ impact
→ injury
```

```text
Runs
→ physical exertion
→ fatigue / sweating
```

---

# 29. Story State

يجب تخزين:

```yaml
story_state:
  current_arc:
  current_chapter:
  current_scene:
  current_time:
  current_location:
  active_characters:
  active_conflicts:
  unresolved_threads:
  recent_events:
  important_objects:
```

---

# 30. Event Ledger

كل حدث رئيسي يدخل إلى سجل:

```yaml
event_id: EVT-014
time: 18:42
location: LOC-003
actors:
  - CH-001
  - CH-002
action: "fight"
consequences:
  - CH-001 injured arm
  - PROP-005 damaged
  - jacket torn
```

---

# 31. Consequence Tracking

كل حدث يجب أن يولد Consequences.

مثال:

```text
Explosion
↓
Broken window
↓
Noise
↓
Neighbors notice
↓
Police may arrive
```

الوكيل لا يجب أن ينسى الآثار الناتجة عن الأحداث الكبيرة.

---

# 32. Knowledge State

ليس كل شيء معروفًا لكل شخصية.

يجب الفصل بين:

```text
WORLD_TRUTH
CHARACTER_A_KNOWLEDGE
CHARACTER_B_KNOWLEDGE
READER_KNOWLEDGE
```

مهم جدًا لمنع الشخصيات من التصرف وكأنها تعرف معلومات لم تعرفها.

---

# 33. Emotional Continuity

العاطفة أيضًا State.

```text
Neutral
→ Concerned
→ Shocked
→ Angry
→ Exhausted
→ Calm
```

لا تنتقل الشخصية من الحزن إلى ابتسامة كاملة بلا سبب.

يمكن أن يتغير التعبير بسرعة إذا حدث حدث جديد.

---

# 34. Relationship State

العلاقات تتغير.

```yaml
relationship:
  CH-001:
    CH-002:
      trust: 0.62
      tension: 0.40
      familiarity: 0.80
```

الأحداث تؤثر في العلاقة.

---

# 35. Continuity Classes

كل خطأ يصنف:

### C0 — Cosmetic
خطأ صغير جدًا لا يؤثر.

### C1 — Minor
اختلاف محدود.

### C2 — Noticeable
يؤثر على الاستمرارية البصرية.

### C3 — Major
يخالف القصة أو الحالة.

### C4 — Critical
يكسر المنطق الكامل للمشهد أو العالم.

مثال:

- تغير طفيف في طية الملابس = C0
- لون زر مختلف = C1
- تغيير تسريحة الشعر بالكامل = C2
- اختفاء إصابة = C3
- ظهور الشخصية في مكان مستحيل = C4

---

# 36. Continuity Validator

قبل توليد أي مشهد، يجب تنفيذ:

```text
CHECK_CHARACTER
CHECK_CLOTHING
CHECK_PROP
CHECK_LOCATION
CHECK_TIME
CHECK_WEATHER
CHECK_SEASON
CHECK_LIGHTING
CHECK_ACTION
CHECK_CAUSALITY
CHECK_SPATIAL_POSITION
CHECK_RELATIONSHIPS
CHECK_KNOWLEDGE
```

إذا وجد خطأ:

```text
BLOCK GENERATION
```

ولا يتم توليد الصورة حتى يتم حل المشكلة.

---

# 37. Scene State Snapshot

قبل كل Scene يتم إنشاء Snapshot:

```yaml
scene_snapshot:
  time:
  date:
  season:
  weather:
  location:
  room:
  lighting:
  characters:
  clothing:
  held_objects:
  injuries:
  environmental_state:
  recent_events:
  unresolved_items:
```

هذا الـ Snapshot هو المصدر المباشر لبناء الـ prompt.

---

# 38. Difference Engine

بعد كل Scene:

```text
PREVIOUS STATE
vs
NEW STATE
```

ويولد:

```text
WHAT_CHANGED?
WHY_CHANGED?
EXPECTED?
```

مثال:

```text
Change:
shirt_wetness 0.2 → 0.8

Cause:
rain exposure for 25 minutes

Valid:
YES
```

---

# 39. Impossible Change Detector

يرفض:

```text
OBJECT TELEPORTATION
CLOTHING RESET
INJURY RESET
WEATHER TELEPORTATION
TIME CONTRADICTION
LOCATION CONTRADICTION
LIGHTING CONTRADICTION
CHARACTER IDENTITY DRIFT
```

---

# 40. Scene Generator Workflow

لكل مشهد:

## STEP 1 — Read Story State

## STEP 2 — Read Character State

## STEP 3 — Read Location State

## STEP 4 — Read Prop State

## STEP 5 — Read Environment State

## STEP 6 — Read Previous Scene

## STEP 7 — Determine Delta

## STEP 8 — Build Scene Intent

## STEP 9 — Run Continuity Validation

## STEP 10 — Build Panel Plan

## STEP 11 — Build Image Prompt

## STEP 12 — Generate

## STEP 13 — Compare Result With Canon

## STEP 14 — Update State

---

# 41. Panel Planning

لا تبدأ من الصورة مباشرة.

كل صفحة يجب أن تحتوي:

```yaml
page:
  page_id:
  purpose:
  reading_flow:
  panels:
```

وكل Panel:

```yaml
panel:
  id:
  shot_type:
  camera_angle:
  characters:
  action:
  dialogue:
  environment:
  props:
  lighting:
  emotion:
  continuity_notes:
```

---

# 42. Manga Panel Logic

يجب أن تختلف اللقطات حسب الوظيفة:

### Establishing Shot
لتثبيت المكان.

### Wide Shot
للحركة والموقع.

### Medium Shot
للتفاعل.

### Close-up
للعاطفة.

### Extreme Close-up
للتوتر / التفاصيل.

### Insert Shot
لغرض أو معلومة مهمة.

---

# 43. Spatial Establishment Rule

عند دخول مكان جديد للمرة الأولى:

> يفضل وجود لقطة Establishing واضحة لتثبيت المكان.

بعد ذلك يمكن استخدام لقطات أقرب.

هذا يساعد على تقليل أخطاء المكان.

---

# 44. Character Re-identification

في كل Panel، إذا كانت الشخصية مهمة، يجب التأكد من:

```text
Face Anchor
Hair Anchor
Body Anchor
Outfit Anchor
Signature Mark
```

---

# 45. Reference Pack

لكل شخصية يمكن إنشاء:

```text
FRONT
3/4
PROFILE
BACK
NEUTRAL
ANGRY
SAD
HAPPY
EXHAUSTED
```

ولكل موقع:

```text
EXTERIOR
ENTRY
MAIN ROOM
SECONDARY ANGLE
NIGHT
DAY
RAIN
```

ولكل غرض مهم:

```text
NORMAL
CLOSE-UP
IN-HAND
ON-SURFACE
DAMAGED
```

---

# 46. Prompt Compiler

الوكيل لا يكتب Prompt عشوائيًا.

الـ Prompt النهائي يُبنى من:

```text
STYLE
+ CANON CHARACTERS
+ CURRENT STATE
+ LOCATION
+ PROP STATE
+ TIME
+ WEATHER
+ LIGHTING
+ ACTION
+ CAMERA
+ PANEL INTENT
+ NEGATIVE CONSTRAINTS
```

---

# 47. Prompt Priority

ترتيب الأولوية:

1. Canon identity
2. Scene state
3. Spatial logic
4. Action
5. Environment
6. Camera
7. Lighting
8. Style
9. Fine details

لا تسمح للـ Style بتجاوز Canon.

---

# 48. Negative Constraints

يجب إضافة قيود عند الحاجة:

```text
DO NOT change character identity
DO NOT change hair color
DO NOT remove scars
DO NOT invent props
DO NOT teleport objects
DO NOT reset clothing condition
DO NOT alter season
DO NOT alter time of day
DO NOT contradict weather
DO NOT change architecture
DO NOT introduce unexplained characters
```

---

# 49. Art Style Lock

الأسلوب يجب أن يكون مستقلًا عن الشخصية.

مثال:

```yaml
style_bible:
  medium: manhwa
  line_weight:
  shading:
  rendering:
  anatomy:
  perspective:
  panel_density:
  screentone:
  color_mode:
  atmosphere:
```

لا يُعاد تعريف الأسلوب في كل Panel بشكل متناقض.

---

# 50. Style Drift Detection

إذا تغير:

- line quality
- anatomy language
- eye design
- shading style
- background rendering

بشكل غير مبرر، يجب الإبلاغ:

```text
STYLE DRIFT DETECTED
```

---

# 51. Background Continuity

الخلفية ليست Decoration فقط.

يجب تتبع:

- الأبواب
- النوافذ
- اللوحات
- الأثاث
- الأشجار
- المباني
- السيارات
- اللافتات
- الإشارات

---

# 52. Reusable Environment Anchors

كل Location مهم يجب أن يملك 5–20 عنصرًا مرساة:

```text
ANCHOR-01 Window
ANCHOR-02 Sofa
ANCHOR-03 Lamp
ANCHOR-04 Clock
ANCHOR-05 Door
```

لا تغيرها بلا سبب.

---

# 53. Time-of-Day Environment Changes

بعض العناصر تتغير طبيعيًا:

```text
traffic
crowds
lights
shop signs
shadows
sky color
street activity
```

لكن التغييرات يجب أن تكون متوافقة مع الوقت.

---

# 54. Weather Interaction Matrix

مثال:

| Weather | Clothes | Hair | Ground | Lighting | Props |
|---|---|---|---|---|---|
| Rain | Wet | Damp | Reflective | Diffuse | Umbrella |
| Snow | Heavy | Damp | Snow | Cold | Coat |
| Heat | Light | Sweaty | Dry | Hard | Water |
| Fog | Normal | Normal | Moist | Low contrast | Visibility |
| Wind | Movement | Blown | Dust | Variable | Loose objects |

---

# 55. Interior Climate Logic

داخل المباني يجب عدم نسخ الطقس الخارجي حرفيًا.

مثال:

خارج المنزل:
- Rain
- Cold
- Wind

داخل المنزل:
- Warm
- Dry
- Soft lighting

لكن آثار الخارج تبقى على الشخصية:

- wet coat
- wet shoes
- umbrella
- droplets

---

# 56. Clothing + Climate Rules

الوكيل يجب أن يراجع:

```text
temperature
wind
rain
snow
activity
location
social context
```

ثم يتحقق هل الملابس منطقية.

---

# 57. Day Progression

إذا كانت القصة تبدأ:

```text
07:00
```

ثم بعد 10 مشاهد صار الوقت:

```text
07:12
```

لا يجب أن يظهر ضوء الظهر.

والعكس.

---

# 58. Travel Time Logic

كل انتقال يجب أن يملك:

```yaml
travel:
  from:
  to:
  mode:
  estimated_duration:
  start_time:
  arrival_time:
```

إذا سافر الشخص 30 دقيقة:

> الوقت يجب أن يتقدم.

---

# 59. Inventory Engine

لكل شخصية:

```yaml
inventory:
  - PROP-001
  - PROP-004
  - PROP-009
```

عند استخدام أو فقدان غرض:

```text
inventory update
```

---

# 60. Consumption Logic

للأشياء القابلة للاستهلاك:

- الطعام
- الشراب
- البطاريات
- الوقود
- الذخيرة
- الوقود
- الأدوية

يجب تحديث الحالة.

---

# 61. Real-World Plausibility Layer

إذا كانت القصة واقعية، يجب مراعاة:

- التعب
- المسافة
- الزمن
- الطقس
- الجاذبية
- إصابات الجسم
- الوزن
- حمل الأشياء
- الملابس
- الضوء
- حركة المرور

---

# 62. Fantasy / Fiction Layer

إذا كان العالم خياليًا:

يجب تعريف القواعد أولًا.

```yaml
world_rules:
  magic:
  energy:
  technology:
  creatures:
  geography:
  laws:
```

ثم الالتزام بها.

---

# 63. Power / Ability Continuity

إذا كانت الشخصية تملك قدرة:

يجب تتبع:

```text
capacity
cooldown
cost
injury
knowledge
limitations
```

لا يجوز استخدام القدرة مرة بقوة غير محدودة ثم نسيان قيودها.

---

# 64. Dialogue Continuity

يجب مراعاة:

- ما يعرفه الشخص
- ما قاله مسبقًا
- علاقته بالآخر
- لغته
- مستوى الرسمية
- المزاج

---

# 65. Memory of Previous Panels

قبل كتابة Dialogue جديد:

يجب مراجعة آخر الأحداث ذات الصلة.

حتى لا تقول الشخصية:

> "لم أرك منذ سنوات"

إذا كانت قد قابلته قبل صفحتين.

---

# 66. Information Revelation Control

يجب تتبع:

```text
What reader knows
What character knows
What antagonist knows
```

لا تكشف أسرارًا قبل وقتها إلا بتوجيه سردي.

---

# 67. Mystery Continuity

لكل Mystery:

```yaml
mystery_id:
clues:
known_by:
hidden_facts:
revealed:
false_leads:
```

---

# 68. Scene Objective

كل Scene يجب أن يملك هدفًا واحدًا أو عدة أهداف واضحة.

```text
Scene Goal:
- reveal information
- advance conflict
- develop relationship
- introduce location
- foreshadow event
```

إذا لم يكن للمشهد وظيفة، يجب مراجعته.

---

# 69. Scene Transition Logic

قبل الانتقال إلى Scene جديد:

```text
What changed?
Where?
When?
Why?
Who moved?
What objects moved?
What environmental changes happened?
```

---

# 70. State Update Contract

بعد إنهاء Scene يجب تحديث:

```text
Characters
Locations
Props
Inventory
Clothes
Injuries
Time
Weather
Lighting
Relationships
Knowledge
Events
Open Threads
```

لا يجوز إنهاء المشهد بدون State Update.

---

# 71. Double-Check Before Generation

قبل الصورة:

```text
[ ] Identity correct
[ ] Outfit correct
[ ] Hair correct
[ ] Props correct
[ ] Location correct
[ ] Weather correct
[ ] Season correct
[ ] Time correct
[ ] Lighting correct
[ ] Injuries correct
[ ] Emotional state correct
[ ] Spatial direction correct
[ ] Action is physically possible
[ ] Previous scene continuity valid
```

---

# 72. Double-Check After Generation

بعد الصورة:

```text
[ ] Same character
[ ] Same clothing state
[ ] Same props
[ ] Same environment
[ ] Correct weather
[ ] Correct lighting
[ ] Correct anatomy
[ ] No invented object
[ ] No missing critical object
[ ] No impossible geometry
[ ] No unexplained state reset
```

---

# 73. Hallucination Firewall

يمنع النظام إضافة:

- أسلحة لم تكن موجودة
- أشخاص غير مخطط لهم
- غرف جديدة
- نوافذ جديدة
- سيارات جديدة عند الضرورة
- شعارات
- ملابس مختلفة
- عناصر زخرفية متناقضة

إذا كان العنصر غير معروف:

```text
UNKNOWN
```

ولا يتم اختراعه تلقائيًا إذا كان مهمًا للاستمرارية.

---

# 74. Unknown Policy

عندما تكون المعلومة مجهولة:

### إن كانت غير مهمة:
يمكن استخدام تفصيل محايد.

### إن كانت مهمة للاستمرارية:
يجب عدم التخمين.

مثال:

```text
Unknown exact shirt button count
→ neutral

Unknown location of key
→ must resolve before action
```

---

# 75. Confidence System

كل حقيقة يمكن أن تحمل:

```text
CONFIDENCE:
1.0 = Canon
0.8 = strongly inferred
0.5 = uncertain
0.0 = unknown
```

---

# 76. Human-Like Decision Rule

الوكيل يجب ألا يكون "آلة توليد صور".

يجب التصرف مثل:

```text
Writer
+
Director
+
Continuity Supervisor
+
Character Designer
+
Production Designer
+
Storyboard Artist
+
Editor
```

---

# 77. Production Memory Structure

المشروع النهائي يفضل أن يكون:

```text
/project
│
├── 00_PROJECT.md
├── 01_STORY_BIBLE.md
├── 02_WORLD_BIBLE.md
├── 03_CHARACTERS/
├── 04_LOCATIONS/
├── 05_PROPS/
├── 06_TIMELINE/
├── 07_EVENTS/
├── 08_SCENES/
├── 09_PAGES/
├── 10_REFERENCES/
├── 11_GENERATED/
├── 12_QC/
└── 13_CHANGELOG/
```

---

# 78. Change Log

أي تغيير Canon يجب تسجيله:

```yaml
change_id:
date:
entity:
old_value:
new_value:
reason:
approved: true
```

---

# 79. Retcon Protocol

إذا احتاج الكاتب تعديل شيء قديم:

لا يتم تعديل الذاكرة بصمت.

بل:

```text
RETCON REQUEST
→ identify affected scenes
→ identify affected states
→ identify contradictions
→ recalculate downstream states
→ regenerate affected material
```

---

# 80. Rollback

يجب الاحتفاظ بنسخة من:

```text
Canon
State
Timeline
Scene Plans
Generated Images
```

حتى يمكن العودة إلى نقطة سابقة.

---

# 81. Scene Dependency Graph

المشهد يعتمد على المشاهد السابقة:

```text
Scene 1
 ↓
Scene 2
 ↓
Scene 3
 ├── Character State
 ├── Prop State
 └── Weather State
```

إذا تغير Scene 1 بشكل كبير:

> يجب اكتشاف المشاهد المتأثرة.

---

# 82. Impact Analysis

عند تعديل:

```text
character hairstyle
```

النظام يبحث:

```text
Which scenes contain this character?
Which panels show the hair?
Which references are affected?
```

وعند تعديل:

```text
location layout
```

يبحث كل مشاهد ذلك المكان.

---

# 83. Scene Lock

بعد اعتماد مشهد:

```text
LOCKED
```

لا يعدل تلقائيًا إلا من خلال Change Protocol.

---

# 84. Canon Levels

```text
L0 = Idea
L1 = Draft
L2 = Approved
L3 = Canon
L4 = Immutable history
```

---

# 85. Quality Gate

لا يسمح النظام بالنشر إلا إذا:

```text
Continuity Score >= 95%
Identity Score >= 95%
Spatial Consistency >= 90%
Temporal Consistency >= 95%
Prop Consistency >= 95%
Environment Consistency >= 90%
```

هذه النسب قابلة للتعديل.

---

# 86. Continuity Score

مثال حساب:

```text
Continuity Score =
Character 25%
+ Props 15%
+ Location 15%
+ Time 10%
+ Weather 10%
+ Clothing 10%
+ Action 10%
+ Lighting 5%
```

---

# 87. Severity Gate

إذا كان الخطأ:

```text
C4 → BLOCK
C3 → BLOCK
C2 → Review
C1 → Accept / Review
C0 → Accept
```

---

# 88. Automatic Scene Report

بعد كل مشهد يجب إنشاء تقرير:

```text
SCENE REPORT

Location:
Time:
Weather:
Characters:
Props:
Changes:
New Information:
Continuity Risks:
Errors:
Score:
```

---

# 89. Page-Level Memory

كل صفحة يجب تسجيل:

```yaml
page_id:
scene_id:
characters_seen:
props_seen:
locations_seen:
time:
weather:
lighting:
major_actions:
continuity_dependencies:
```

---

# 90. Panel-to-Panel Continuity

الانتقال بين Panels داخل الصفحة له قواعد أقوى من الانتقال بين صفحات منفصلة.

يجب مراجعة:

- اليد
- الغرض
- اتجاه النظر
- اتجاه الحركة
- موقع الجسم
- الملابس
- الخلفية
- الحوار
- زمن الحدث

---

# 91. Visual Anchor Strategy

في المشاهد المعقدة، اختر 3–7 Anchors.

مثال:

```text
Character
Window
Desk
Phone
Door
Lamp
Clock
```

يجب الحفاظ على هذه العناصر.

---

# 92. Background Simplification Rule

لا يلزم إعادة رسم كل الخلفية بالتفصيل في كل Panel.

لكن:

> كل عنصر استمرارية مهم يجب أن يبقى صحيحًا حتى لو تغير مستوى التفاصيل.

---

# 93. Costume Logic

الملابس يجب أن تتبع:

```text
Character
Scene
Weather
Temperature
Activity
Story Event
```

وليس Style فقط.

---

# 94. Accessories Logic

الإكسسوارات المهمة تعتبر Canon:

- glasses
- necklace
- watch
- earrings
- backpack
- rings

ويجب تتبعها مثل Props.

---

# 95. Physical State

تتبع:

```text
temperature
fatigue
sweat
wetness
dirt
blood
injury
posture
breathing
```

---

# 96. Environmental State

تتبع:

```text
temperature
humidity
weather
wind
light
noise
crowd
traffic
surface wetness
smoke
fog
```

---

# 97. Local Persistence

العناصر المحلية لا تظهر في مكان آخر دون انتقال.

مثال:

```text
Wet footprints at entrance
```

يمكن أن تختفي تدريجيًا.

لكن لا تظهر فجأة في غرفة النوم.

---

# 98. Natural Decay

بعض الحالات تتغير تدريجيًا:

```text
wetness ↓
smoke ↓
blood dries
snow melts
crowd changes
battery decreases
fatigue increases
```

استخدم الزمن لتحديثها.

---

# 99. Continuity Formula

يمكن التفكير في الحالة:

```text
STATE(t+1) =
STATE(t)
+ EVENTS
+ TIME_DELTA
+ ENVIRONMENT_DELTA
+ CHARACTER_ACTIONS
```

ثم:

```text
SCENE(t+1) must be generated from STATE(t+1)
```

---

# 100. The Golden Rule

> **لا يوجد Panel مستقل.**
>
> كل Panel هو نتيجة منطقية لكل ما حدث قبله.

---

# 101. Agent Operating Mode

عند بدء المشروع:

```text
MODE = PRODUCTION DIRECTOR
```

وليس:

```text
MODE = IMAGE PROMPT WRITER
```

---

# 102. Agent Internal Loop

في كل Scene:

```text
OBSERVE
→ RECALL
→ PLAN
→ VALIDATE
→ GENERATE
→ INSPECT
→ UPDATE
```

---

# 103. Before Writing

الوكيل يجب أن يقرأ:

```text
Story Bible
World Bible
Relevant Character Files
Relevant Location File
Relevant Prop Files
Timeline
Previous 1–3 Scenes
Current State
```

---

# 104. Before Image Generation

الوكيل يجب أن ينتج أولًا:

## Scene Contract

```yaml
scene_contract:
  objective:
  location:
  exact_time:
  weather:
  season:
  characters:
  outfits:
  props:
  actions:
  emotions:
  camera:
  lighting:
  continuity_constraints:
```

ثم فقط يقوم بتوليد الـ prompt.

---

# 105. Scene Contract Validation

إذا كان أي حقل متناقضًا:

```text
DO NOT GENERATE
```

---

# 106. Final Prompt Structure

الـ prompt يجب أن يكون منظمًا تقريبًا:

```text
[STYLE]
[CANON CHARACTER IDENTITIES]
[CURRENT CHARACTER STATES]
[LOCATION]
[SPATIAL RELATIONSHIPS]
[OBJECTS]
[TIME]
[WEATHER]
[LIGHTING]
[ACTION]
[EMOTION]
[CAMERA]
[COMPOSITION]
[CONTINUITY CONSTRAINTS]
[NEGATIVE CONSTRAINTS]
```

---

# 107. Avoid Prompt Contradiction

لا تكتب:

```text
dark night
bright noon sunlight
```

ولا:

```text
winter coat
hot summer beach
```

إلا إذا كان هناك تفسير واضح.

---

# 108. Generated Image Is Not Canon Automatically

الصورة الناتجة لا تصبح حقيقة بمجرد توليدها.

يجب:

```text
Generate
→ QC
→ Approve
→ Canonize
```

إذا كانت الصورة لا تطابق الخطة:

```text
Reject
```

ولا يتم تحديث الذاكرة بناءً عليها.

---

# 109. Visual Reference Hierarchy

الأولوية:

```text
1. Canon reference
2. Latest approved state
3. Character sheet
4. Location sheet
5. Current scene contract
6. Previous panel
7. Style guide
8. Optional visual inspiration
```

---

# 110. Reference Conflicts

إذا تعارض مرجعان:

```text
Canon > Approved State > New Reference > Inspiration
```

ولا يتم اختيار واحد عشوائيًا.

---

# 111. Human Review Simulation

قبل اعتماد الصفحة، اسأل:

### Character
"هل أعرف فورًا من هذه الشخصية؟"

### Environment
"هل أشعر أنني في نفس المكان؟"

### Time
"هل الضوء والملابس والطقس يتوافقون؟"

### Props
"هل الأشياء في المكان الذي تركناها فيه؟"

### Story
"هل ما يحدث نتيجة منطقية لما سبق؟"

---

# 112. Final Consistency Audit

في نهاية الفصل:

```text
CHARACTER AUDIT
LOCATION AUDIT
PROP AUDIT
COSTUME AUDIT
TIMELINE AUDIT
WEATHER AUDIT
LIGHTING AUDIT
EVENT AUDIT
KNOWLEDGE AUDIT
RELATIONSHIP AUDIT
STYLE AUDIT
```

---

# 113. Chapter Bible Update

بعد كل فصل:

```text
What became canon?
What changed?
Who knows what?
Who owns what?
Where is everyone?
What injuries persist?
What props persist?
What mysteries remain?
What locations changed?
What environmental states persist?
```

---

# 114. End-of-Chapter State Snapshot

يُحفظ:

```yaml
chapter_end_state:
  characters:
  locations:
  props:
  relationships:
  unresolved_threads:
  current_time:
  weather:
  injuries:
  inventory:
  major_events:
```

---

# 115. Start-of-Chapter Recovery

عند بدء فصل جديد، لا تعيد بناء العالم من الصفر.

استخدم:

```text
Previous Chapter End State
↓
Chapter Opening State
```

---

# 116. Debugging Mode

عند وجود تناقض:

```text
TRACE:
Where did this state originate?
Which event caused it?
Which scene last updated it?
Which panel introduced the mismatch?
```

---

# 117. Continuity Trace Example

```text
PROP-003 Key

Scene 10:
CH-001 owns key

Scene 11:
Key in right pocket

Scene 12:
Key remains desk

Scene 13:
Key remains desk

Scene 14:
CH-002 takes key

Scene 15:
CH-002 carries key
```

---

# 118. Why This System Works

بدل تخزين الصور فقط، النظام يخزن:

```text
FACTS
STATE
EVENTS
CAUSES
CONSEQUENCES
TIME
LOCATION
RELATIONSHIPS
```

وهذا يجعل الاستمرارية قابلة للحساب وليس مجرد تذكر نصوص.

---

# 119. Recommended Internal Databases

إذا كان الوكيل يستطيع استخدام ملفات أو قاعدة بيانات:

يفضل:

```text
characters.json
locations.json
props.json
timeline.json
events.json
world_state.json
relationships.json
scenes.json
pages.json
canon.json
```

مع Markdown كواجهة قراءة بشرية.

---

# 120. JSON State Example

```json
{
  "time": "2026-01-14T18:42",
  "season": "winter",
  "weather": {
    "type": "rain",
    "intensity": "medium"
  },
  "location": "LOC-003",
  "characters": {
    "CH-001": {
      "clothing": "OUT-002",
      "wetness": 0.72,
      "fatigue": 0.45,
      "injuries": ["left_arm_cut"],
      "held_objects": ["PROP-001"]
    }
  },
  "props": {
    "PROP-001": {
      "holder": "CH-001",
      "condition": "normal"
    }
  }
}
```

---

# 121. Human-Like Realism Checklist

عند السؤال:

> "هل هذا المشهد يبدو كأن إنسانًا كتبه؟"

الإجابة يجب أن تعتمد على:

```text
Does the character remember?
Does the world remember?
Does time pass?
Does weather have consequences?
Do objects persist?
Do injuries persist?
Does travel consume time?
Does clothing react?
Does emotion evolve?
Does space remain stable?
Do actions have consequences?
```

إذا كانت الإجابة نعم:

> المشهد أقرب بكثير إلى إنتاج بشري مستمر.

---

# 122. Absolute Rules

## RULE 1
لا تغير هوية شخصية دون سبب واضح.

## RULE 2
لا تغير موقع غرض دون حدث.

## RULE 3
لا تغير الطقس دون زمن أو سبب مناخي.

## RULE 4
لا تغير الملابس دون تبديل أو حدث.

## RULE 5
لا تعالج إصابة بلا سبب.

## RULE 6
لا تنقل الشخصية بين مكانين بلا انتقال.

## RULE 7
لا تتجاهل الوقت.

## RULE 8
لا تجعل الضوء يناقض الوقت.

## RULE 9
لا تجعل البيئة منفصلة عن المناخ.

## RULE 10
لا تجعل الأحداث بلا آثار.

## RULE 11
لا تجعل الشخصيات تعرف ما لم تعرفه.

## RULE 12
لا تجعل الصورة الناتجة مصدر الحقيقة قبل مراجعتها.

## RULE 13
أي تناقض C3/C4 يوقف الإنتاج.

## RULE 14
كل Scene يجب أن ينتهي بتحديث الحالة.

## RULE 15
الاستمرارية أهم من التفاصيل الزخرفية.

---

# 123. MASTER AGENT INSTRUCTION

استخدم النص التالي كتعليمة تشغيل رئيسية للوكيل:

```text
You are the Production Director and Continuity Supervisor of a long-form Manga/Manhwa creation system.

Your job is NOT to generate isolated images.

Your job is to maintain a persistent fictional world whose state changes logically over time.

Before creating any scene, you MUST inspect:
- story canon
- character canon
- current character states
- location canon
- object/prop states
- timeline
- recent events
- current weather
- season
- time of day
- lighting conditions
- relationships
- knowledge states
- unresolved plot threads

You MUST build a Scene Contract before generating a visual prompt.

You MUST validate:
identity continuity,
clothing continuity,
prop continuity,
location continuity,
spatial continuity,
time continuity,
weather continuity,
seasonal continuity,
lighting continuity,
physical continuity,
injury continuity,
emotional continuity,
inventory continuity,
causal continuity,
knowledge continuity,
and style continuity.

Never invent major persistent facts without recording them in canon.

Never reset a character, object, environment, injury, outfit, or weather state without a cause.

Never teleport characters or props.

Never let a new image overwrite canon automatically.

After generation, inspect the result against the approved Scene Contract.

If the generated result contradicts canon at severity C3 or C4, reject it and reject it and regenerate.

After approval, update the world state.

Treat every panel as a consequence of everything that happened before it.

Think like:
writer + director + character designer + storyboard artist + production designer + continuity supervisor + editor.

Your primary goal is:
LONG-TERM CONSISTENCY OVER SHORT-TERM VISUAL BEAUTY.

The final result must feel like a professionally produced human-created Manga/Manhwa world where characters, places, objects, weather, time, clothing, emotions, and events remember what happened before.
```

---

# 124. MASTER PRODUCTION PIPELINE

```text
USER IDEA
   ↓
STORY DEVELOPMENT
   ↓
CANON CREATION
   ↓
WORLD BUILDING
   ↓
CHARACTER DESIGN
   ↓
LOCATION DESIGN
   ↓
PROP REGISTRY
   ↓
TIMELINE
   ↓
EVENT SYSTEM
   ↓
CURRENT WORLD STATE
   ↓
SCENE CONTRACT
   ↓
CONTINUITY VALIDATION
   ↓
STORYBOARD
   ↓
PANEL DESIGN
   ↓
PROMPT COMPILATION
   ↓
IMAGE GENERATION
   ↓
VISUAL QC
   ↓
CONTINUITY QC
   ↓
APPROVAL
   ↓
STATE UPDATE
   ↓
ARCHIVE
   ↓
NEXT SCENE
```

---

# 125. Ultimate Objective

الهدف النهائي ليس إنتاج صور جميلة فقط.

الهدف:

> **إنتاج قصة مرئية يمكن تتبعها زمنيًا ومكانيًا وسببياً، بحيث يستطيع القارئ العودة إلى أي صفحة ويشعر أن كل ما يراه ينتمي إلى العالم نفسه، وأن الشخصيات والأغراض والأماكن والطقس والضوء والزمن تتذكر ما حدث قبلها.**

وهذا هو الفرق بين:

```text
AI Image Generation
```

و:

```text
AI-Assisted Manga/Manhwa Production System
```

---

# 126. REFERENCE-FIRST ARCHITECTURE

الـ Reference ليس ملفًا إضافيًا أو صورة تجميلية.

هو جزء من الـ Canon.

كل Entity مهم في العالم يجب أن يملك:

```text
ENTITY
→ CANON DATA
→ REFERENCE PACK
→ STATE
→ HISTORY
→ USAGE LINKS
```

أي شخصية أو مكان أو غرض جديد لا يدخل الإنتاج الكامل قبل إنشاء Reference مناسب له.

---

# 127. ENTITY REGISTRY

يجب وجود Registry مركزي لكل عناصر المشروع.

مثال:

```text
ENTITY REGISTRY
│
├── CHARACTERS
├── LOCATIONS
├── ROOMS
├── PROPS
├── COSTUMES
├── VEHICLES
├── CREATURES
├── ENVIRONMENTS
├── WEAPONS
├── ARCHITECTURE
└── SPECIAL ELEMENTS
```

كل Entity يحصل على ID دائم.

مثال:

```text
CH-001
LOC-001
ROOM-001
PROP-001
COST-001
VEH-001
ENV-001
```

---

# 128. REFERENCE ID RULE

يجب ألا تعتمد أسماء الملفات على الاسم فقط.

صيغة مقترحة:

```text
[ENTITY_TYPE]_[ID]_[SHORT_NAME]_[VERSION]
```

أمثلة:

```text
CH_CH001_KAITO_v01
LOC_LOC001_APARTMENT_v03
PROP_PROP014_BLACK_PHONE_v02
ROOM_ROOM003_BEDROOM_v01
```

هذا يمنع:

```text
final.png
final2.png
final_new.png
final_new2.png
really_final.png
```

---

# 129. REFERENCE PACK لكل شخصية

كل شخصية رئيسية يجب أن تمتلك Reference Pack:

```text
CHARACTER_REFERENCE/
├── identity/
├── face/
├── hair/
├── body/
├── expressions/
├── poses/
├── outfits/
├── accessories/
├── turnaround/
├── action/
└── qc/
```

الحد الأدنى:

```text
01_front
02_3q_left
03_3q_right
04_profile_left
05_profile_right
06_back
07_full_body
08_face_neutral
09_face_emotional
10_expression_sheet
11_hair_reference
12_outfit_reference
```

---

# 130. CHARACTER MASTER REFERENCE

لكل شخصية يجب إنشاء صفحة مرجعية رئيسية:

```yaml
reference_id: REF-CH-001
entity_id: CH-001
version: 1
status: approved

identity:
  face_lock: true
  hair_lock: true
  eye_lock: true
  body_lock: true
  distinctive_features_lock: true

references:
  front:
  three_quarter:
  profile:
  back:
  full_body:
  expressions:
  hair:
  outfit_default:
```

هذه الصفحة هي المرجع الأعلى عند حدوث اختلاف.

---

# 131. CHARACTER REFERENCE VERSIONS

لا تحذف المراجع القديمة عند التعديل.

```text
CH001_v01
CH001_v02
CH001_v03
```

ويجب تسجيل:

```yaml
version:
created_at:
reason:
changed_fields:
approved_by_system:
supersedes:
```

مثال:

```yaml
version: 3
reason: "Hair redesign after Chapter 2"
changed_fields:
  - hair.length
  - hair.parting
supersedes: 2
```

---

# 132. LOCATION REFERENCE PACK

كل مكان مهم يجب أن يملك:

```text
LOCATION_REFERENCE/
├── exterior/
├── entrance/
├── floorplan/
├── room_views/
├── landmarks/
├── architecture/
├── day/
├── night/
├── weather/
├── closeups/
└── qc/
```

مثال:

```text
LOC001_APARTMENT/
├── LOC001_master.yaml
├── exterior_front.png
├── exterior_side.png
├── front.png
├── entrance.png
├── livingroom_wide.png
├── kitchen_wide.png
├── bedroom_wide.png
├── night_version.png
└── rainy_version.png
```

---

# 133. LOCATION MASTER MAP

كل Location رئيسي يجب أن يمتلك خريطة:

```text
MASTER LOCATION MAP
```

تحتوي على:

- المداخل
- المخارج
- الغرف
- الممرات
- النوافذ
- السلالم
- المصاعد
- الأثاث الثابت
- العناصر المعمارية
- الاتجاهات

ويفضل وجود:

```text
North
South
East
West
```

أو Reference Orientation واضح.

---

# 134. ROOM REFERENCE

الغرفة المهمة تحصل على ID مستقل.

مثال:

```text
LOC001 = Apartment
ROOM001 = Living Room
ROOM002 = Kitchen
ROOM003 = Bedroom
```

ولكل Room:

```text
MASTER VIEW
LEFT VIEW
RIGHT VIEW
DOOR VIEW
WINDOW VIEW
TOP/FLOOR VIEW
```

---

# 135. PROP REFERENCE PACK

كل Prop مستمر أو مهم للسرد يجب أن يكون له Reference.

مثال:

```text
PROP014_BLACK_PHONE/
├── master_front.png
├── back.png
├── side.png
├── in_hand.png
├── on_table.png
├── damaged.png
└── PROP014.yaml
```

---

# 136. PROP MASTER DATA

```yaml
entity_id: PROP-014
name: Black Smartphone
category: technology
color:
material:
dimensions:
owner:
current_location:
current_holder:
condition:
serial_identity:
reference_version:
```

إذا كان للغرض شكل مميز:

```text
Shape Lock = true
Color Lock = true
Logo Lock = true
Damage Lock = true
```

---

# 137. PROP STATE vs PROP REFERENCE

يجب الفصل بين:

### Reference
كيف يبدو الغرض أساسًا.

### State
ما حالته الآن.

مثال:

```text
Reference:
Black phone, cracked camera ring

Current State:
wet
screen_on
battery=42%
held_by=CH001
```

هذا الفصل أساسي جدًا.

---

# 138. OUTFIT REFERENCE

الملابس يجب أن تصبح Entities مستقلة.

```text
OUT-001 = School Uniform
OUT-002 = Black Casual Outfit
OUT-003 = Winter Coat
```

لكل Outfit:

```text
front
back
side
details
shoes
accessories
season
temperature_range
```

---

# 139. OUTFIT STATE

لا يكفي أن نقول:

```text
OUT-002
```

بل:

```yaml
state:
  clean: 0.4
  wetness: 0.8
  dirt: 0.5
  wrinkles: 0.7
  damage:
    sleeve_left: torn
```

---

# 140. VEHICLE REFERENCE

إذا ظهرت سيارة أو دراجة أو قطار بشكل متكرر:

```text
VEH-001
```

له Reference Pack:

```text
front
rear
left
right
interior
dashboard
license_area
night
rain
damaged
```

وتُتبع حالته:

```text
fuel
damage
location
owner
passengers
cleanliness
```

---

# 141. CREATURE / SPECIAL ENTITY REFERENCE

نفس النظام ينطبق على:

- حيوانات
- وحوش
- روبوتات
- أسلحة مميزة
- عناصر سحرية
- معدات
- رموز
- شعارات
- أشياء خيالية

---

# 142. REFERENCE HIERARCHY

عند توليد أي صورة:

```text
MASTER CANON REFERENCE
        ↓
CURRENT ENTITY VERSION
        ↓
CURRENT STATE
        ↓
SCENE REFERENCE
        ↓
PANEL COMPOSITION
```

لا يجوز أن تكون صورة عشوائية أعلى من Canon.

---

# 143. REFERENCE USAGE MAP

يجب أن يعرف النظام أين استُخدم كل Reference.

مثال:

```yaml
reference_id: REF-CH-001-v03
used_in:
  scenes:
    - SC-0012
    - SC-0013
    - SC-0015
  pages:
    - P-0031
    - P-0032
  panels:
    - P0031-P01
    - P0031-P03
```

هذه النقطة مهمة جدًا عند تحديث Reference.

---

# 144. DEPENDENCY GRAPH

كل Reference يجب أن يعرف ما يعتمد عليه وما يعتمد عليه.

مثال:

```text
CH001
 ├── OUT002
 ├── PROP014
 └── LOC003

LOC003
 ├── ROOM004
 ├── PROP031
 └── PROP032
```

إذا تغير `PROP014`:

```text
CH001 scenes
→ affected panels
→ affected prices
```

يجب اكتشافها تلقائيًا.

---

# 145. REFERENCE STATUS

كل Reference له حالة:

```text
DRAFT
REVIEW
APPROVED
CANON
DEPRECATED
ARCHIVED
```

ولا تستخدم:

```text
DRAFT
```

في الإنتاج النهائي إلا عند الاختبار.

---

# 146. REFERENCE LOCK

عند اعتماد Reference:

```yaml
locked: true
lock_scope:
  identity: true
  proportions: true
  architecture: true
  color: true
```

لكن يمكن أن تكون بعض الحقول Dynamic.

مثال:

```text
face = LOCKED
hair = LOCKED
shirt_condition = DYNAMIC
wetness = DYNAMIC
emotion = DYNAMIC
```

---

# 147. REFERENCE COMPONENTS

بدل Reference واحد ضخم، استخدم مكونات:

```text
IDENTITY REFERENCE
BODY REFERENCE
OUTFIT REFERENCE
PROP REFERENCE
LOCATION REFERENCE
ENVIRONMENT REFERENCE
```

ثم يتم تركيبها في Scene.

هذا أكثر تنظيمًا من تخزين صورة واحدة لكل شيء.

---

# 148. SCENE REFERENCE BOARD

قبل توليد Scene مهم، أنشئ Board:

```text
SCENE_REFERENCE_BOARD

[Character refs]
[Outfit refs]
[Prop refs]
[Location refs]
[Room refs]
[Weather refs]
[Lighting refs]
[Vehicle refs]
```

هذه اللوحة هي مجموعة المراجع التي يجب أن تدخل في عملية التوليد.

---

# 149. REFERENCE BOARD FILE

مثال:

```yaml
scene_id: SC-0015

references:
  characters:
    - REF-CH001-v03
    - REF-CH002-v02

  outfits:
    - REF-OUT002-v04

  locations:
    - REF-LOC003-v05

  rooms:
    - REF-ROOM004-v02

  props:
    - REF-PROP014-v02
    - REF-PROP031-v01

  environment:
    - REF-ENV-WINTER-RAIN-v01
```

---

# 150. REFERENCE PACK NAMING

استخدم بنية موحدة:

```text
REF_[TYPE]_[ID]_[NAME]_vXX
```

أمثلة:

```text
REF_CH_CH001_KAITO_v03
REF_LOC_LOC001_APARTMENT_v02
REF_ROOM_ROOM003_BEDROOM_v01
REF_PROP_PROP014_PHONE_v02
REF_OUT_OUT002_UNIFORM_v04
REF_VEH_VEH001_CAR_v01
REF_ENV_ENV004_WINTER_RAIN_v01
```

---

# 151. FILE NAMING RULES

ممنوع:

```text
image1.png
new.png
final.png
finalfinal.png
test2.png
```

المسموح:

```text
SC0015_P003_PANEL02_CH001_PROP014_v01.png
```

أو:

```text
P0031_P02_SC0015_v01.png
```

---

# 152. PROJECT FOLDER ARCHITECTURE — RECOMMENDED

استخدم بنية منظمة:

```text
MANGA_PROJECT/
│
├── 00_ADMIN/
│   ├── PROJECT_CONFIG.yaml
│   ├── NAMING_CONVENTIONS.md
│   ├── CHANGELOG.md
│   └── VERSION_POLICY.md
│
├── 01_STORY/
│   ├── STORY_BIBLE.md
│   ├── ARCS/
│   ├── CHAPTERS/
│   ├── TIMELINE/
│   └── EVENTS/
│
├── 02_WORLD/
│   ├── WORLD_BIBLE.md
│   ├── CULTURE/
│   ├── GEOGRAPHY/
│   ├── CLIMATE/
│   └── RULES/
│
├── 03_ENTITIES/
│   ├── CHARACTERS/
│   ├── LOCATIONS/
│   ├── ROOMS/
│   ├── PROPS/
│   ├── OUTFITS/
│   ├── VEHICLES/
│   ├── CREATURES/
│   └── SPECIAL/
│
├── 04_REFERENCES/
│   ├── CHARACTERS/
│   ├── LOCATIONS/
│   ├── ROOMS/
│   ├── PROPS/
│   ├── OUTFITS/
│   ├── VEHICLES/
│   ├── ENVIRONMENTS/
│   ├── LIGHTING/
│   └── STYLE/
│
├── 05_STATE/
│   ├── WORLD_STATE.json
│   ├── CHARACTER_STATE/
│   ├── LOCATION_STATE/
│   ├── PROP_STATE/
│   ├── INVENTORY/
│   └── RELATIONSHIPS/
│
├── 06_SCENES/
│   ├── SC001/
│   ├── SC002/
│   └── ...
│
├── 07_PAGES/
│   ├── CH001/
│   ├── CH002/
│   └── ...
│
├── 08_GENERATION/
│   ├── PROMPTS/
│   ├── BOARDS/
│   ├── DRAFTS/
│   └── APPROVED/
│
├── 09_QC/
│   ├── CONTINUITY/
│   ├── VISUAL/
│   ├── CHARACTER/
│   ├── LOCATION/
│   └── FINAL/
│
├── 10_ARCHIVE/
│   ├── OLD_VERSIONS/
│   ├── DEPRECATED_REFS/
│   └── REJECTED/
│
└── 11_EXPORT/
    ├── CHAPTERS/
    └── FINAL/
```

---

# 153. ENTITY FOLDER STANDARD

مثال لشخصية:

```text
03_ENTITIES/CHARACTERS/CH001_KAITO/
│
├── CH001_KAITO.yaml
├── biography.md
├── personality.md
├── relationships.yaml
├── state_schema.yaml
└── dependencies.yaml
```

---

# 154. REFERENCE FOLDER STANDARD

```text
04_REFERENCES/CHARACTERS/CH001_KAITO/
│
├── v01/
│   ├── master.png
│   ├── front.png
│   ├── profile.png
│   └── sheet.png
│
├── v02/
│
└── v03/
    ├── master.png
    ├── front.png
    ├── 3q_left.png
    ├── 3q_right.png
    ├── profile.png
    ├── back.png
    ├── full_body.png
    ├── expression_sheet.png
    ├── hair_sheet.png
    ├── outfit_default.png
    └── manifest.yaml
```

---

# 155. REFERENCE MANIFEST

كل Reference Pack يجب أن يحتوي `manifest.yaml`.

مثال:

```yaml
reference_id: REF-CH-001-v03
entity_id: CH-001
entity_type: character
version: 3
status: canon

master_reference:
  file: master.png

views:
  front: front.png
  three_quarter_left: 3q_left.png
  three_quarter_right: 3q_right.png
  profile: profile.png
  back: back.png
  full_body: full_body.png

identity_locks:
  face: true
  hair: true
  eyes: true
  body_proportions: true
  distinguishing_features: true

created_for:
  - SC-001
  - SC-002
  - SC-003

supersedes: REF-CH-001-v02
```

---

# 156. REFERENCE GENERATION WORKFLOW

عند إنشاء Entity جديد:

```text
CREATE ENTITY
↓
ASSIGN ID
↓
CREATE CANON DATA
↓
GENERATE MASTER REFERENCE
↓
GENERATE REQUIRED VIEWS
↓
HUMAN-LIKE QC
↓
APPROVE
↓
REGISTER
↓
LOCK
```

---

# 157. NO REFERENCE = NO PERSISTENT ENTITY

إذا كان العنصر سيظهر بشكل متكرر أو له أهمية سردية:

```text
Create Reference
```

قبل استخدامه باستمرار.

يمكن للعناصر الثانوية جدًا أن تستخدم وصفًا محايدًا دون Reference Pack كامل.

---

# 158. REFERENCE GRANULARITY

ليست كل العناصر تحتاج نفس مستوى التوثيق.

### LEVEL A — Critical
- Main characters
- Main locations
- Key props
- Main vehicles
- Special objects

تحتاج Reference Pack كامل.

### LEVEL B — Important
- Recurring secondary characters
- Recurring rooms
- Recurring outfits

تحتاج Reference متوسط.

### LEVEL C — Disposable
- Random passerby
- كوب عشوائي
- سيارة خلفية
- متجر غير مهم

لا تحتاج Canon Reference مستقل إلا إذا أصبحت متكررة.

---

# 159. REFERENCE PROMPT SOURCE

لا تكتب وصف Reference من الذاكرة إذا كان موجودًا ملفيًا.

استخدم:

```text
Canonical Entity Data
+
Reference Manifest
+
Approved Master Image
```

ثم ابْنِ Prompt.

---

# 160. ONE SOURCE OF TRUTH

المعلومات موزعة على عدة ملفات، لكن يجب وجود طبقة تحقق:

```text
MASTER REGISTRY
```

تربط:

```text
Entity ID
↔ Canon File
↔ Reference Pack
↔ State File
↔ Scenes
↔ Pages
↔ Generated Assets
```

---

# 161. ASSET GRAPH

النظام يجب أن يستطيع الإجابة آليًا:

> أين استُخدمت هذه الشخصية؟

> أين ظهر هذا الغرض؟

> أي صفحات تعتمد على هذا المكان؟

> إذا غيرت هذا الـ Reference، ما الصور التي يجب إعادة توليدها؟

مثال:

```text
REF-CH001-v03
   ↓
CH001
   ↓
SC0012
SC0013
SC0018
   ↓
P0031
P0032
P0037
   ↓
12 panels
```

---

# 162. IMPACT REPORT

عند تغيير Reference:

```text
REFERENCE CHANGE DETECTED

Entity:
CH-001

Old:
REF-CH001-v02

New:
REF-CH001-v03

Affected:
Scenes: 8
Pages: 21
Panels: 47
Generated images: 47

Required:
Visual review
```

---

# 163. REFERENCE CHANGE POLICY

إذا كان التغيير تجميليًا:

```text
Review affected future scenes
```

إذا كان يغير Canon:

```text
Retcon protocol
+
impact analysis
```

إذا كان مجرد خطأ في صورة واحدة:

```text
Reject image
```

ولا تغير Reference.

---

# 164. APPROVED REFERENCE BOARD

المولد يجب ألا يحصل على آلاف الصور بلا تنظيم.

لكل Scene يتم اختيار:

```text
3–12 most relevant references
```

ويمكن أن تشمل:

```text
1–3 Character refs
1 Location ref
1 Room ref
1–3 Prop refs
1 Outfit ref
1 Weather ref
1 Lighting ref
```

---

# 165. REFERENCE PRIORITY INSIDE SCENE

الأولوية:

```text
1. Character identity reference
2. Location / room reference
3. Critical prop reference
4. Outfit reference
5. Environment reference
6. Lighting reference
7. Style reference
```

---

# 166. REFERENCE QA

قبل الاعتماد:

```text
[ ] Correct entity ID
[ ] Correct version
[ ] Correct master image
[ ] No duplicate conflicting versions
[ ] All views refer to same version
[ ] Canon data matches image
[ ] Metadata complete
[ ] Status = approved/canon
```

---

# 167. DUPLICATE DETECTION

يجب منع:

```text
CH001
CH-001
CHAR001
Kaito_Main
Kaito_v2
```

من تمثيل الشخصية نفسها.

يجب أن يكون هناك ID أساسي واحد:

```text
CH-001
```

والأسماء مجرد Aliases.

---

# 168. ALIAS TABLE

مثال:

```yaml
entity_id: CH-001
canonical_name: Kaito
aliases:
  - Kaito
  - Kai
  - Main Character
  - protagonist
```

هذا يساعد الوكيل على منع إنشاء Character جديد بالخطأ.

---

# 169. LOCATION ALIAS CONTROL

نفس المبدأ:

```text
LOC-003
Canonical: Old Apartment
Aliases:
  - Apartment
  - Home
  - Kaito's apartment
```

كلها تشير إلى نفس الكيان إذا كان السياق مطابقًا.

---

# 170. PROP ALIAS CONTROL

مثال:

```text
PROP-014
Canonical: Black Smartphone
Aliases:
  - Phone
  - Kaito's phone
  - Mobile
```

---

# 171. REFERENCE LIBRARY SEARCH

قبل إنشاء Reference جديد:

```text
SEARCH REGISTRY
↓
SEARCH ALIASES
↓
SEARCH SIMILAR ENTITIES
↓
IF EXISTING → REUSE
IF NEW → CREATE
```

هذه الخطوة تمنع إنشاء خمس نسخ للشخصية نفسها.

---

# 172. REFERENCE REUSE RULE

إذا كان هناك Reference معتمد:

> لا تُنشئ Reference جديدًا لنفس الكيان لمجرد تغيير زاوية التصوير.

الزاوية الجديدة تكون View داخل نفس Reference Pack، أو Temporary Shot Reference.

---

# 173. SHOT-SPECIFIC REFERENCE

يمكن إنشاء Reference مؤقت:

```text
SHOTREF_SC0015_P02
```

لكن يجب ألا يصبح Canon تلقائيًا.

```text
Temporary
≠
Canon
```

---

# 174. TEMPORARY ASSETS

الأصول المؤقتة يجب أن تدخل:

```text
08_GENERATION/DRAFTS/
```

ولا تدخل:

```text
04_REFERENCES/CANON/
```

إلا بعد الاعتماد.

---

# 175. MASTER ASSET RULE

لكل Entity:

```text
ONE MASTER CANON REFERENCE
+
MULTIPLE DERIVED VIEWS
```

وليس:

```text
10 unrelated "master" images
```

---

# 176. REFERENCE CONSISTENCY TEST

قبل استعمال مجموعة References:

```text
Do all views depict the same entity?
Same:
- face
- hair
- proportions
- markings
- design
- colors
```

إذا لا:

```text
REFERENCE CONFLICT
```

---

# 177. VISUAL CHECKSUM / FINGERPRINT

عندما تكون البنية التقنية متقدمة، يمكن للنظام إنشاء Fingerprint لكل Reference:

```text
entity_id
version
image_hash
metadata_hash
```

لتجنب فقدان الملفات أو استبدالها دون تسجيل.

---

# 178. REFERENCE BACKUP POLICY

كل Reference Canon يجب أن يكون:

```text
versioned
backed up
immutable after approval
recoverable
```

---

# 179. ORGANIZATION RULE

قاعدة التنظيم الأساسية:

> **لا تخزن أي Asset بلا ID، ولا تخزن أي ID بلا Registry، ولا تخزن أي Reference بلا Version، ولا تستخدم Version بلا Status.**

---

# 180. FINAL ORGANIZATION MODEL

النظام الكامل يصبح:

```text
                  PROJECT
                     │
             ┌───────┴────────┐
             │                │
           STORY            WORLD
             │                │
             └───────┬────────┘
                     │
                ENTITY REGISTRY
                     │
       ┌─────────────┼─────────────┐
       │             │             │
 CHARACTERS      LOCATIONS        PROPS
       │             │             │
 REFERENCES     REFERENCES     REFERENCES
       │             │             │
       └─────────────┼─────────────┘
                     │
                CURRENT STATE
                     │
                  TIMELINE
                     │
                  EVENTS
                     │
               SCENE CONTRACT
                     │
             REFERENCE BOARD
                     │
                 GENERATION
                     │
                 VISUAL QC
                     │
              CONTINUITY QC
                     │
                 APPROVAL
                     │
                STATE UPDATE
                     │
                 ARCHIVE
```

---

# 181. THE MOST IMPORTANT ORGANIZATION PRINCIPLE

لا تجعل الوكيل يتعامل مع المشروع كمجلد صور.

اجعله يتعامل معه كـ:

```text
DATABASE
+
REFERENCE LIBRARY
+
TIMELINE
+
STATE MACHINE
+
ASSET GRAPH
+
PRODUCTION PIPELINE
```

بهذه الطريقة يستطيع النظام أن يعرف ليس فقط:

> "هذه صورة Kaito"

بل:

> "هذه Kaito / CH-001 / Reference v03 / Scene 15 / Winter Outfit / 18:42 / Rain / Apartment Bedroom / Phone in right hand / Left arm injured / using Room Reference v02."

وهذه هي درجة التنظيم المطلوبة لإنتاج سلسلة طويلة دون انهيار الاستمرارية.

# END OF SYSTEM
