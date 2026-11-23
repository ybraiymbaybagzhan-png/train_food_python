/**
 * DAR | RES group - Official Website & Digital QR Menu
 * Core JavaScript Logic & Complete Multilingual Dataset
 * Built strictly according to "Меню А3 новое.pdf" and brand guidelines.
 */

// ==========================================
// 1. COMPLETE RESTAURANT MENU DATA (Page 1)
// ==========================================
const RESTAURANT_MENU_DATA = [
  // --- Таңғы ас | Завтраки | Breakfast ---
  {
    id: "bf-1",
    category: "breakfast",
    price: 800,
    weight: "250 гр",
    names: {
      kz: "Күріш ботқасы",
      ru: "Каша рисовая",
      en: "Rice porridge"
    },
    descriptions: {
      kz: "Сүт пен сары май қосылып пісірілген дәстүрлі дәмді күріш ботқасы.",
      ru: "Традиционная нежная рисовая каша на молоке со сливочным маслом.",
      en: "Traditional tender rice porridge cooked with fresh milk and butter."
    },
    image: null
  },
  {
    id: "bf-2",
    category: "breakfast",
    price: 800,
    weight: "250 гр",
    names: {
      kz: "Тары ботқасы",
      ru: "Каша пшенная",
      en: "Millet porridge"
    },
    descriptions: {
      kz: "Сүт пен сары май қосылған хош иісті, үлпілдек тары ботқасы.",
      ru: "Ароматная рассыпчатая пшенная каша на молоке со сливочным маслом.",
      en: "Fragrant wholesome millet porridge cooked with milk and butter."
    },
    image: null
  },
  {
    id: "bf-3",
    category: "breakfast",
    price: 800,
    weight: "250 гр",
    names: {
      kz: "Сұлы жармасы",
      ru: "Каша овсяная",
      en: "Oatmeal porridge"
    },
    descriptions: {
      kz: "Жолдағы таңертеңгі пайдалы әрі тойымды сүтке пісірілген сұлы ботқасы.",
      ru: "Полезная классическая овсяная каша на молоке для сытного утра в пути.",
      en: "Nutritious classic rolled oats cooked with milk for a healthy train breakfast."
    },
    image: null
  },
  {
    id: "bf-4",
    category: "breakfast",
    price: 800,
    weight: "150 гр",
    names: {
      kz: "Қуырылған жұмыртқа",
      ru: "Яичница",
      en: "Fried sunny-side eggs"
    },
    descriptions: {
      kz: "Балғын жұмыртқалардан қуырылған классикалық көзді жұмыртқа.",
      ru: "Классическая яичница-глазунья из свежих яиц, обжаренная до золотистого края.",
      en: "Classic sunny-side up fried farm eggs with golden yolks."
    },
    image: null
  },
  {
    id: "bf-5",
    category: "breakfast",
    price: 1300,
    weight: "180 гр",
    names: {
      kz: "Шұжық қосылған жұмыртқа",
      ru: "Яичница с сосиской или колбасой",
      en: "Fried eggs with sausage"
    },
    descriptions: {
      kz: "Қызартып қуырылған дәмді шұжықпен дайындалған тойымды жұмыртқа.",
      ru: "Сытная горячая яичница с обжаренными сочными сосисками или колбасой.",
      en: "Hearty pan-fried eggs served with browned savory sausage."
    },
    image: "assets/food_breakfast.jpg"
  },
  {
    id: "bf-6",
    category: "breakfast",
    price: 900,
    weight: "150 гр",
    names: {
      kz: "Құймақ (3 дана)",
      ru: "Блины (порция 3 шт.)",
      en: "Pancakes (3 pcs)"
    },
    descriptions: {
      kz: "Сары май немесе балғын джеммен ұсынылатын үйдегідей жұмсақ құймақтар.",
      ru: "Домашние кружевные блинчики со сливочным маслом или джемом.",
      en: "Three golden homestyle crepe pancakes served warm with butter or jam."
    },
    image: "assets/food_breakfast.jpg"
  },
  {
    id: "bf-7",
    category: "breakfast",
    price: 300,
    weight: "60 гр",
    names: {
      kz: "Піскен жұмыртқа (1 дана)",
      ru: "Вареное яйцо (1 шт.)",
      en: "Boiled egg (1 pc)"
    },
    descriptions: {
      kz: "Сапардағы таңғы асқа арналған жаңа пісірілген жұмыртқа.",
      ru: "Свежесваренное яйцо к сытному дорожному завтраку.",
      en: "Fresh boiled farm egg served warm as a breakfast classic."
    },
    image: null
  },

  // --- Холодные закуски | Appetizers ---
  {
    id: "app-1",
    category: "appetizers",
    price: 2100,
    weight: "300 гр",
    names: {
      kz: "Кавказ закускасы",
      ru: "Кавказская закуска",
      en: "Caucasian snack platter"
    },
    descriptions: {
      kz: "Балғын қызанақтар, қытырлақ қиярлар, зәйтүн, нәзік брынза ірімшігі мен аскөк.",
      ru: "Свежие спелые помидоры, хрустящие огурцы, маслины, нежная брынза и зелень.",
      en: "Ripe tomatoes, crunchy cucumbers, olives, rich brynza cheese, and fresh garden herbs."
    },
    image: null
  },
  {
    id: "app-2",
    category: "appetizers",
    price: 2000,
    weight: "250 гр",
    names: {
      kz: "Маринадталған көкөністер",
      ru: "Домашние разносолы",
      en: "Homemade pickled vegetables"
    },
    descriptions: {
      kz: "Қытырлақ тұздалған қиярлар, маринадталған черри және ашытылған қырыққабат ассортиі.",
      ru: "Ассорти из хрустящих соленых огурчиков, маринованных черри и квашеной капусты.",
      en: "Crispy barrel pickles, marinated cherry tomatoes, and seasoned sauerkraut."
    },
    image: null
  },
  {
    id: "app-3",
    category: "appetizers",
    price: 3800,
    weight: "300 гр",
    names: {
      kz: "Ассорти ет (қазы мен ет тілімі)",
      ru: "Мясное ассорти",
      en: "Assorted gourmet meat platter"
    },
    descriptions: {
      kz: "Дәстүрлі жылқы еті қазысы, қақталған сиыр еті және таңдаулы шұжық тілімдері.",
      ru: "Изысканная нарезка из традиционного казы, сыровяленого мяса и деликатесных колбас.",
      en: "Fine selection of traditional kazy, cured beef, and cold sliced meats."
    },
    image: null
  },

  // --- Бірінші тамақ | Первые блюда | First courses ---
  {
    id: "soup-1",
    category: "first-courses",
    price: 2200,
    weight: "350 гр",
    names: {
      kz: "Сорпа (етпен)",
      ru: "Суп с мясом (Сорпа)",
      en: "Traditional beef soup (Sorpa)"
    },
    descriptions: {
      kz: "Таңдаулы сиыр етінен баяу қайнатылған хош иісті, құнарлы мөлдір сорпа.",
      ru: "Наваристый прозрачный бульон из отборной говядины с овощами и душистой зеленью.",
      en: "Rich, slow-simmered beef broth with tender meat cuts and herbs."
    },
    image: null
  },
  {
    id: "soup-2",
    category: "first-courses",
    price: 2500,
    weight: "400 гр",
    names: {
      kz: "Сұйық үй лағманы",
      ru: "Лагман по-домашнему",
      en: "Homestyle liquid lagman"
    },
    descriptions: {
      kz: "Қолдан созылған ұзын кеспе, сиыр еті мен көкөністер қосылған шырынды лағман.",
      ru: "Тянутая вручную лапша в ароматном бульоне с кусочками говядины и сладким перцем.",
      en: "Hand-pulled noodles served in rich broth with beef chunks, bell peppers, and spices."
    },
    image: null
  },
  {
    id: "soup-3",
    category: "first-courses",
    price: 2000,
    weight: "350 гр",
    names: {
      kz: "Дәстүрлі борщ сорпасы",
      ru: "Борщ со сметаной",
      en: "Classic Borsch with sour cream"
    },
    descriptions: {
      kz: "Қызылша, қырыққабат пен жұмсақ еттен дайындалған, қаймақпен ұсынылатын классикалық борщ.",
      ru: "Классический наваристый борщ на мясном бульоне с сочной свеклой и ложкой сметаны.",
      en: "Rich beetroot soup cooked on savory meat broth, served with fresh sour cream."
    },
    image: null
  },
  {
    id: "soup-4",
    category: "first-courses",
    price: 2000,
    weight: "350 гр",
    names: {
      kz: "Үй кеспесі",
      ru: "Лапша по-домашнему (Кеспе)",
      en: "Homemade chicken noodle soup"
    },
    descriptions: {
      kz: "Тауық етінің алтын түстес сорпасында дайындалған жұмсақ үй кеспесі.",
      ru: "Легкий золотистый бульон с нежной курицей и домашней тонко нарезанной лапшой.",
      en: "Tender chicken and thin hand-cut noodles in golden savory broth."
    },
    image: null
  },
  {
    id: "soup-5",
    category: "first-courses",
    price: 2200,
    weight: "350 гр",
    names: {
      kz: "Тұшпара сорпасымен",
      ru: "Пельмени с бульоном",
      en: "Dumplings in broth"
    },
    descriptions: {
      kz: "Қолдан түйілген дәмді ет тұшпарасы, хош иісті сорпа және жаңа аскөкпен.",
      ru: "Горячие мясные пельмени ручной лепки в согревающем наваристом бульоне с зеленью.",
      en: "Handcrafted minced meat dumplings served in steaming seasoned broth."
    },
    image: null
  },
  {
    id: "soup-6",
    category: "first-courses",
    price: 2000,
    weight: "350 гр",
    names: {
      kz: "Рассольник сорпасы",
      ru: "Рассольник",
      en: "Rassolnik barley soup"
    },
    descriptions: {
      kz: "Арпа жармасы, тұздалған қияр мен сиыр етінен әзірленген дәстүрлі дәмді сорпа.",
      ru: "Ароматный традиционный суп с перловой крупой, солеными огурчиками и нежным мясом.",
      en: "Traditional hearty soup with pearl barley, pickles, and tender beef."
    },
    image: null
  },
  {
    id: "soup-7",
    category: "first-courses",
    price: 2200,
    weight: "350 гр",
    names: {
      kz: "Құрама ет солянкасы",
      ru: "Солянка мясная",
      en: "Meat Solyanka soup"
    },
    descriptions: {
      kz: "Қақталған түрлі еттер, зәйтүн және лимон қосылған қышқылтым-ащы қою сорпа.",
      ru: "Густой пряный суп из нескольких сортов копченостей, маслин, каперсов и дольки лимона.",
      en: "Rich, spicy-sour soup featuring assorted smoked meats, olives, and fresh lemon."
    },
    image: null
  },

  // --- Салаттар | Салаты | Salads ---
  {
    id: "salad-1",
    category: "salads",
    price: 2200,
    weight: "200 гр",
    names: {
      kz: "Тауық еті қосылған цезарь салаты",
      ru: "Цезарь с курицей",
      en: "Chicken Caesar salad"
    },
    descriptions: {
      kz: "Қытырлақ айсберг жапырақтары, нәзік тауық еті, черри қызанақтары және пармезан.",
      ru: "Хрустящие листья романо, сочное куриное филе, томаты черри, пармезан и соус цезарь.",
      en: "Crisp romaine, grilled chicken breast, cherry tomatoes, shaved parmesan, and croutons."
    },
    image: "assets/food_caesar.jpg"
  },
  {
    id: "salad-2",
    category: "salads",
    price: 2200,
    weight: "250 гр",
    names: {
      kz: "Оливье дәстүрлі салаты",
      ru: "Оливье классический",
      en: "Classic Olivier salad"
    },
    descriptions: {
      kz: "Пісірілген картоп, сәбіз, жасыл бұршақ және шұжық қосылған классикалық салат.",
      ru: "Любимый праздничный салат из отварного картофеля, моркови, зеленого горошка и соуса.",
      en: "Traditional recipe with diced potatoes, tender carrots, peas, and creamy dressing."
    },
    image: null
  },
  {
    id: "salad-3",
    category: "salads",
    price: 1700,
    weight: "200 гр",
    names: {
      kz: "Балғын көкөніс салаты",
      ru: "Свежий овощной салат",
      en: "Fresh garden salad"
    },
    descriptions: {
      kz: "Балғын қызанақ, қияр, пияз және жаңа үзілген аскөк қосылған дәруменді салат.",
      ru: "Летний хрустящий салат из сладких помидоров, огурцов, репчатого лука и зелени.",
      en: "Crisp cucumbers, sweet ripe tomatoes, red onions, and fresh parsley dressing."
    },
    image: null
  },
  {
    id: "salad-4",
    category: "salads",
    price: 2200,
    weight: "250 гр",
    names: {
      kz: "Грек салаты",
      ru: "Греческий салат",
      en: "Authentic Greek salad"
    },
    descriptions: {
      kz: "Балғын көкөністер, майлы брынза ірімшігі, зәйтүн және зәйтүн майы.",
      ru: "Крупно нарезанные сочные овощи с кубиками соленой брынзы, маслинами и орегано.",
      en: "Crisp cucumbers, sweet peppers, tomatoes, black olives, and rich feta cheese."
    },
    image: null
  },
  {
    id: "salad-5",
    category: "salads",
    price: 1000,
    weight: "250 гр",
    names: {
      kz: "Корейше сәбіз салаты",
      ru: "Морковь по-корейски",
      en: "Spicy Korean-style carrots"
    },
    descriptions: {
      kz: "Дәмдеуіштер, сарымсақ және хош иісті маймен дайындалған ащылау сәбіз салаты.",
      ru: "Пикантная тонко натертая морковь с чесноком, кориандром и пряным маслом.",
      en: "Julienned fresh carrots marinated with aromatic coriander, garlic, and hot oil."
    },
    image: null
  },
  {
    id: "salad-6",
    category: "salads",
    price: 2200,
    weight: "180 гр",
    names: {
      kz: "Пекин салаты",
      ru: "Пекинский салат",
      en: "Beijing beef salad"
    },
    descriptions: {
      kz: "Қытырлақ пекин қырыққабаты, сиыр еті, тәтті бұрыш және күнжіт майы тұздығы.",
      ru: "Хрустящая пекинская капуста, нежная говядина, сладкий перец и кунжутная заправка.",
      en: "Crispy napa cabbage, sauteed beef strips, bell peppers, and sesame dressing."
    },
    image: null
  },
  {
    id: "salad-7",
    category: "salads",
    price: 2200,
    weight: "250 гр",
    names: {
      kz: "Малибу фирмалық салаты",
      ru: "Малибу фирменный салат",
      en: "Malibu signature salad"
    },
    descriptions: {
      kz: "Қақталған тауық еті, тәтті жүгері, қатты ірімшік, қияр және қытырлақ сухарилер.",
      ru: "Копченая курочка, сладкая кукуруза, твердый сыр, свежие огурцы и сухарики.",
      en: "Smoked chicken breast, sweet corn, melted cheese notes, cucumber, and crisp croutons."
    },
    image: null
  },
  {
    id: "salad-8",
    category: "salads",
    price: 1500,
    weight: "200 гр",
    names: {
      kz: "Ащышық қызанақ салаты",
      ru: "Ачичук салат",
      en: "Achichuk tomato salad"
    },
    descriptions: {
      kz: "Жұқалап туралған балғын қызанақтар, қызыл пияз және райхан қосылған дәстүрлі салат.",
      ru: "Тончайше нарезанные спелые сладкие томаты со сладким фиолетовым луком и базиликом.",
      en: "Paper-thin sweet vine tomatoes, purple onions, and herbs, perfect for pilaf."
    },
    image: null
  },

  // --- Негізгі тағамдар | Вторые блюда | Second courses ---
  {
    id: "main-1",
    category: "main-courses",
    price: 2200,
    weight: "170 гр",
    names: {
      kz: "Жұмыртқа қосылған бифштекс",
      ru: "Бифштекс с яйцом",
      en: "Beefsteak with fried egg"
    },
    descriptions: {
      kz: "Таңдаулы сиыр етінен пісірілген шырынды бифштекс және үстіндегі көзді жұмыртқа.",
      ru: "Сочный бифштекс из рубленой говядины, увенчанный аппетитным жареным яйцом.",
      en: "Juicy minced beef patty grilled to perfection and topped with a sunny fried egg."
    },
    image: null
  },
  {
    id: "main-2",
    category: "main-courses",
    price: 2000,
    weight: "140 гр",
    names: {
      kz: "Үйдегідей сиыр еті котлеттері",
      ru: "Котлеты домашние",
      en: "Homestyle beef cutlets"
    },
    descriptions: {
      kz: "Құнарлы сиыр етінен қуырылған, шырынды әрі жұмсақ үй котлеттері.",
      ru: "Золотистые сочные котлеты из отборной говядины по проверенному домашнему рецепту.",
      en: "Golden pan-seared ground beef cutlets made with fresh onion and herbs."
    },
    image: null
  },
  {
    id: "main-3",
    category: "main-courses",
    price: 3500,
    weight: "250 гр",
    names: {
      kz: "Дәстүрлі қазақша қуырдақ",
      ru: "Куырдак по-казахски",
      en: "Traditional Kazakh Kuyrdak"
    },
    descriptions: {
      kz: "Ет, картоп және пиязбен қазанда шыжғырылып қуырылған дәстүрлі қазақ тағамы.",
      ru: "Традиционное сытное жаркое из нежного мяса с картофелем, луком и специями.",
      en: "Tender meat braised in a skillet with golden potatoes, sweet onions, and spices."
    },
    image: null
  },
  {
    id: "main-4",
    category: "main-courses",
    price: 2300,
    weight: "300 гр",
    names: {
      kz: "Мерекелік палау",
      ru: "Плов праздничный",
      en: "Festive meat pilaf (Plov)"
    },
    descriptions: {
      kz: "Таңдаулы ет, сары сәбіз, зире және мейізбен бұқтырылған хош иісті мерекелік палау.",
      ru: "Ароматный восточный плов с отборным мясом, сладкой желтой морковью и барбарисом.",
      en: "Fragrant long-grain rice pilaf simmered with tender meat, yellow carrots, and spices."
    },
    image: "assets/food_plov.jpg"
  },
  {
    id: "main-5",
    category: "main-courses",
    price: 2600,
    weight: "200 гр",
    names: {
      kz: "Тауықтан дайындалған чахохбили",
      ru: "Чахохбили из курицы",
      en: "Chicken Chakhohbili stew"
    },
    descriptions: {
      kz: "Қызанақ, сарымсақ және күнзе тұздығында бұқтырылған шырынды тауық еті.",
      ru: "Ароматное рагу из кусочков курицы, тушенных в густом томатном соусе с чесноком и кинзой.",
      en: "Tender chicken simmered in rich tomato, garlic, and fragrant cilantro sauce."
    },
    image: null
  },
  {
    id: "main-6",
    category: "main-courses",
    price: 2500,
    weight: "250 гр",
    names: {
      kz: "Буда піскен етті мәнті",
      ru: "Манты с мясом (паровые)",
      en: "Steamed meat manti"
    },
    descriptions: {
      kz: "Қолдан жайылған қамыр, туралған ет пен пиязбен толтырылған будағы ыстық мәнті.",
      ru: "Сочные манты ручной лепки с рубленым мясом и луком, приготовленные на пару.",
      en: "Steamed delicate dough pockets generously filled with seasoned minced meat and onions."
    },
    image: null
  },
  {
    id: "main-7",
    category: "main-courses",
    price: 3100,
    weight: "250 гр",
    names: {
      kz: "Тай стиліндегі сиыр еті",
      ru: "Мясо по-тайски",
      en: "Thai-style wok beef"
    },
    descriptions: {
      kz: "Тәтті бұрыш, соя тұздығы және күнжітпен вокта қуырылған жұмсақ сиыр еті.",
      ru: "Нежные полоски говядины, обжаренные в воке со сладким перцем и соусом терияки.",
      en: "Stir-fried beef strips with crisp bell peppers, sweet soy sauce, and scallions."
    },
    image: null
  },
  {
    id: "main-8",
    category: "main-courses",
    price: 2800,
    weight: "300 гр",
    names: {
      kz: "Гуйру қуырылған лағман",
      ru: "Гуйру лагман",
      en: "Guiru stir-fried lagman"
    },
    descriptions: {
      kz: "Қолмен созылған кеспе, қуырылған сиыр еті және шырынды көкөністер подливімен.",
      ru: "Тянутая вручную лапша с крупно обжаренной говядиной, сельдереем и сочными овощами.",
      en: "Hand-pulled noodles topped with wok-seared beef chunks, celery, and peppers."
    },
    image: null
  },
  {
    id: "main-9",
    category: "main-courses",
    price: 2800,
    weight: "300 гр",
    names: {
      kz: "Цомян қуырылған лағман",
      ru: "Цомян лагман",
      en: "Tsomyan pan-fried lagman"
    },
    descriptions: {
      kz: "Ет, бұрыш және дәмдеуіштермен бірге табада қуырылған қытырлақ кеспе лағманы.",
      ru: "Лапша, обжаренная вместе с мясом и хрустящими овощами в ароматном воке.",
      en: "Handmade noodles pan-fried together with tender beef slices and crunchy vegetables."
    },
    image: null
  },
  {
    id: "main-10",
    category: "main-courses",
    price: 2100,
    weight: "200 гр",
    names: {
      kz: "Пеште пісірілген тауық сирағы",
      ru: "Окорочок запеченный",
      en: "Roasted golden chicken leg"
    },
    descriptions: {
      kz: "Қызарып піскен қытырлақ қабығы бар, пеште дәмделген шырынды тауық еті.",
      ru: "Сочный куриный окорочок, запеченный в духовке до хрустящей румяной корочки.",
      en: "Oven-roasted chicken quarter with crispy seasoned skin and juicy tender meat."
    },
    image: null
  },

  // --- Гарнирлер | Гарниры | Garnish ---
  {
    id: "side-1",
    category: "side-dishes",
    price: 650,
    weight: "150 гр",
    names: {
      kz: "Үлпілдек картоп езбесі",
      ru: "Картофельное пюре",
      en: "Creamy mashed potatoes"
    },
    descriptions: {
      kz: "Сүт пен сары май қосылып езілген нәзік, ауызда еритін картоп пюресі.",
      ru: "Воздушное домашнее картофельное пюре со сливочным маслом и молоком.",
      en: "Velvety whipped mashed potatoes prepared with fresh cream and butter."
    },
    image: null
  },
  {
    id: "side-2",
    category: "side-dishes",
    price: 1500,
    weight: "150 гр",
    names: {
      kz: "Қытырлақ фри картобы",
      ru: "Картофель фри",
      en: "Crisp French fries"
    },
    descriptions: {
      kz: "Алтын түске дейін қуырылған қытырлақ әрі ыстық фри картобы.",
      ru: "Горячие хрустящие золотистые брусочки картофеля с мелкой морской солью.",
      en: "Hot golden-fried potato sticks with a crunchy exterior and fluffy interior."
    },
    image: null
  },
  {
    id: "side-3",
    category: "side-dishes",
    price: 650,
    weight: "150 гр",
    names: {
      kz: "Буда піскен күріш",
      ru: "Рис отварной",
      en: "Steamed white rice"
    },
    descriptions: {
      kz: "Буда пісірілген үгілмелі, майдаланбайтын ақ ұзын күріш.",
      ru: "Рассыпчатый длиннозерный белый рис, приготовленный на пару.",
      en: "Fluffy, tender steamed long-grain white rice."
    },
    image: null
  },
  {
    id: "side-4",
    category: "side-dishes",
    price: 650,
    weight: "150 гр",
    names: {
      kz: "Қарақұмық ботқасы",
      ru: "Гречка отварная",
      en: "Buttered buckwheat"
    },
    descriptions: {
      kz: "Сары май қосылып пісірілген үгілмелі әрі дәмді қарақұмық гарнирі.",
      ru: "Ароматная рассыпчатая гречневая каша со сливочным маслом.",
      en: "Wholesome, fluffy buckwheat kasha tossed with savory butter."
    },
    image: null
  },
  {
    id: "side-5",
    category: "side-dishes",
    price: 650,
    weight: "150 гр",
    names: {
      kz: "Пісірілген макарон",
      ru: "Макароны отварные",
      en: "Buttered pasta"
    },
    descriptions: {
      kz: "Сары маймен ұсынылатын классикалық жұмсақ әрі дәмді макарон.",
      ru: "Классические макароны твердых сортов со сливочным маслом.",
      en: "Al dente durum wheat pasta lightly tossed with melting butter."
    },
    image: null
  }
];

// ==========================================
// 2. COMPLETE BAR MENU DATA (Page 2)
// ==========================================
const BAR_MENU_DATA = [
  // --- Ыстық сусындар | Горячие напитки | Hot drinks ---
  {
    id: "bar-hot-1",
    category: "hot-drinks",
    price: 300,
    volume: "1 шыны / чашка",
    names: {
      kz: "Шай (қара немесе көк)",
      ru: "Чай (черный или зеленый)",
      en: "Tea (black or green cup)"
    },
    descriptions: {
      kz: "Сапарда жанға қуат беретін ыстық қара немесе көк шай шынысы.",
      ru: "Классический листовой горячий чай на выбор: крепкий черный или освежающий зеленый.",
      en: "Freshly brewed hot black or soothing green tea in a cup."
    }
    image: "assets/menu/hd-01.jpg"
  },
  {
    id: "bar-hot-2",
    category: "hot-drinks",
    price: 400,
    volume: "1 шыны / чашка",
    names: {
      kz: "Сүт қосқан немесе лимонды шай",
      ru: "Чай с молоком или лимоном",
      en: "Tea with milk or lemon"
    },
    descriptions: {
      kz: "Қазақы сүтпен немесе қышқылтым лимон тілімімен ұсынылатын хош иісті шай.",
      ru: "Бодрящий чай со свежим молоком по-казахски или с ароматной долькой лимона.",
      en: "Hot brewed tea served with rich fresh milk or tangy lemon slice."
    }
    image: "assets/menu/hd-02.jpg"
  },
  {
    id: "bar-hot-3",
    category: "hot-drinks",
    price: 900,
    volume: "Шәйнек / Чайник",
    names: {
      kz: "Шәйнек қара/көк шай",
      ru: "Чайник чая листового",
      en: "Teapot of freshly brewed tea"
    },
    descriptions: {
      kz: "Купедегі жайлы әңгімеге арналған үлкен шәйнекпен ұсынылатын ыстық шай.",
      ru: "Большой согревающий чайник свежезаваренного листового чая для долгой беседы в купе.",
      en: "Full teapot of loose-leaf black or green tea for a cozy train journey."
    }
    image: "assets/menu/hd-03.jpg"
  },
  {
    id: "bar-hot-4",
    category: "hot-drinks",
    price: 1000,
    volume: "Шәйнек / Чайник",
    names: {
      kz: "Сүт қосқан шәйнек шай",
      ru: "Чайник чая с молоком",
      en: "Teapot of milk tea"
    },
    descriptions: {
      kz: "Дәстүрлі қазақы үлгіде дайындалған мол сүтті ыстық шай шәйнегі.",
      ru: "Традиционный чайник чая с натуральным деревенским молоком по казахским традициям.",
      en: "Traditional pot of rich black tea brewed with fresh milk."
    }
    image: "assets/menu/hd-04.jpg"
  },
  {
    id: "bar-hot-5",
    category: "hot-drinks",
    price: 1800,
    volume: "Шәйнек / Чайник",
    names: {
      kz: "Ташкент шайы (фирмалық)",
      ru: "Ташкентский чай фирменный",
      en: "Tashkent signature tea"
    },
    descriptions: {
      kz: "Жалбыз, лимон және нават қосылған әйгілі хош иісті ташкенттік шай шәйнегі.",
      ru: "Знаменитый чайник зеленого и черного чая со свежей мятой, дольками лимона и наватом.",
      en: "Famous blend of black and green tea with fresh mint leaves, lemon slices, and sugar crystals."
    }
    image: "assets/menu/hd-05.jpg"
  },
  {
    id: "bar-hot-6",
    category: "hot-drinks",
    price: 700,
    volume: "1 шыны / чашка",
    names: {
      kz: "Сүт қосқан кофе",
      ru: "Кофе с молоком",
      en: "Coffee with milk"
    },
    descriptions: {
      kz: "Таңертеңгі сергектік сыйлайтын сүт қосылған хош иісті ыстық кофе.",
      ru: "Ароматный согревающий кофе с нежным вспененным молоком.",
      en: "Hot aromatic brewed coffee with smooth steamed milk."
    }
    image: "assets/menu/hd-06.jpg"
  },
  {
    id: "bar-hot-7",
    category: "hot-drinks",
    price: 400,
    volume: "1 шыны / чашка",
    names: {
      kz: "MacTea / MacCoffee 3 в 1",
      ru: "MacTea / MacCoffee 3 в 1",
      en: "MacTea / MacCoffee 3-in-1"
    },
    descriptions: {
      kz: "Жол үстінде тез дайындалатын тәтті әрі сергіткіш 3-і 1-де ыстық сусын.",
      ru: "Популярный растворимый горячий напиток 3 в 1 для быстрого согревания в пути.",
      en: "Quick hot instant coffee or tea beverage with sweet creamer."
    }
    image: "assets/menu/hd-07.jpg"
  },

  // --- Шайға | К чаю | For tea ---
  {
    id: "bar-tea-1",
    category: "for-tea",
    price: 700,
    volume: "1 порция",
    names: {
      kz: "Қытырлақ вафли мен печенье",
      ru: "Вафли и печенье к чаю",
      en: "Crispy wafers and cookies"
    },
    descriptions: {
      kz: "Шай ішуге арналған тәтті сүзбе вафлилері мен үгілмелі печеньелер.",
      ru: "Хрустящие сладкие вафли со сливочной начинкой и рассыпчатое сахарное печенье.",
      en: "Crunchy cream-filled wafers and golden butter cookies for tea time."
    }
    image: "assets/menu/tea-01.jpg"
  },
  {
    id: "bar-tea-2",
    category: "for-tea",
    price: 800,
    volume: "1 дана / шт",
    names: {
      kz: "Альбени шоколадты печеньесі",
      ru: "Печенье Альбени (Albeni)",
      en: "Albeni caramel chocolate cookies"
    },
    descriptions: {
      kz: "Сүтті шоколадпен қапталған, ішінде созылмалы карамелі бар танымал печенье.",
      ru: "Популярное печенье в молочном шоколаде с тягучей карамелью внутри.",
      en: "Crisp biscuit bars coated with milk chocolate and chewy caramel."
    }
    image: "assets/menu/tea-02.jpg"
  },
  {
    id: "bar-tea-3",
    category: "for-tea",
    price: 1400,
    volume: "1 плитка",
    names: {
      kz: "Қазақстандық шоколад / Alpen Gold",
      ru: "Шоколад Казахстанский / Alpen Gold",
      en: "Kazakhstan chocolate bar"
    },
    descriptions: {
      kz: "Шайға арналған нағыз қазақстандық сүтті немесе қара шоколад тақтасы.",
      ru: "Плитка отборного молочного или темного шоколада к приятному чаепитию.",
      en: "Classic Kazakhstan iconic premium chocolate bar or Alpen Gold."
    }
    image: "assets/menu/tea-03.jpg"
  },
  {
    id: "bar-tea-4",
    category: "for-tea",
    priceDisplay: "600 / 900 ₸",
    price: 600,
    volume: "1 дана / шт",
    names: {
      kz: "Сникерс / Твикс батончиктері",
      ru: "Батончики Сникерс / Твикс",
      en: "Snickers / Twix candy bars"
    },
    descriptions: {
      kz: "Жержаңғақ, карамель және қытырлақ печенье қосылған тәтті батончиктер.",
      ru: "Любимые питательные шоколадные батончики с арахисом, карамелью или печеньем.",
      en: "Classic chocolate candy bars packed with roasted peanuts, caramel, or biscuit."
    }
    image: "assets/menu/tea-04.jpg"
  },
  {
    id: "bar-tea-5",
    category: "for-tea",
    price: 1000,
    volume: "1 дана / шт",
    names: {
      kz: "Тәтті бәліш (десерттік пирожное)",
      ru: "Пирожное десертное",
      en: "Gourmet pastry cake"
    },
    descriptions: {
      kz: "Ыстық шайға арналған кремді нәзік бисквитті тәтті пирожное.",
      ru: "Нежное слоеное или бисквитное пирожное с кремовой прослойкой к горячему чаю.",
      en: "Delicate layered sponge pastry cake with rich sweet cream."
    }
    image: "assets/menu/tea-05.jpg"
  },
  {
    id: "bar-tea-6",
    category: "for-tea",
    price: 1200,
    volume: "1 қаптама / уп",
    names: {
      kz: "Яшкино дәмді круассандары",
      ru: "Круассаны Яшкино",
      en: "Yashkino flaky croissants"
    },
    descriptions: {
      kz: "Шоколадты немесе кремді салмасы бар үлпілдек мини-круассандар.",
      ru: "Воздушные слоеные мини-круассаны с нежной кремовой или шоколадной начинкой.",
      en: "Flaky golden miniature croissants filled with creamy chocolate filling."
    }
    image: "assets/menu/tea-06.jpg"
  },

  // --- Нан өнімдері | Выпечка | Bakery products ---
  {
    id: "bar-bake-1",
    category: "bakery",
    price: 400,
    volume: "Себет / Корзина",
    names: {
      kz: "Нан себеті",
      ru: "Хлебная корзина",
      en: "Fresh bread basket"
    },
    descriptions: {
      kz: "Ыстық тағамдар мен сорпаларға арналған жаңа піскен ақ және қара нан тілімдері.",
      ru: "Свежий нарезной белый и ржаной хлеб к горячим блюдам и супам.",
      en: "Assortment of freshly sliced white and wheat table breads."
    }
    image: "assets/menu/bk-01.jpg"
  },
  {
    id: "bar-bake-2",
    category: "bakery",
    price: 400,
    volume: "1 дана / шт",
    names: {
      kz: "Картоп немесе қырыққабат бәліштері",
      ru: "Пирожки с картошкой или капустой",
      en: "Pirozhki with potato or cabbage"
    },
    descriptions: {
      kz: "Дәмді ашыған қамырдан пеште пісірілген ыстық үй пирожкилері.",
      ru: "Теплые домашние пирожки из нежного дрожжевого теста с сытной начинкой.",
      en: "Warm oven-baked soft yeast pastries stuffed with seasoned potato or cabbage."
    }
    image: "assets/menu/bk-02.jpg"
  },
  {
    id: "bar-bake-3",
    category: "bakery",
    price: 500,
    volume: "1 дана / шт",
    names: {
      kz: "Қамырда пісірілген шұжық",
      ru: "Сосиски в тесте",
      en: "Sausage baked in dough"
    },
    descriptions: {
      kz: "Алтын түстес үлпілдек қамырға оралып пісірілген шырынды шұжық.",
      ru: "Аппетитная сочная сосиска, запеченная в мягком золотистом тесте.",
      en: "Juicy hot dog sausage wrapped in golden, soft baked dough."
    }
    image: "assets/menu/bk-03.jpg"
  },
  {
    id: "bar-bake-4",
    category: "bakery",
    price: 400,
    volume: "1 дана / шт",
    names: {
      kz: "Тәтті пісірілген тоқаш",
      ru: "Булочка сдобная",
      en: "Sweet bakery bun"
    },
    descriptions: {
      kz: "Пештен жаңа шыққан хош иісті, жұмсақ әрі тәтті сүзбе тоқаш.",
      ru: "Свежевыпеченная сладкая сдобная булочка с румяной сахарной корочкой.",
      en: "Soft, golden-baked sweet breakfast bun with a light glaze."
    }
    image: "assets/menu/bk-04.jpg"
  },
  {
    id: "bar-bake-5",
    category: "bakery",
    price: 2600,
    volume: "1 дана / шт",
    names: {
      kz: "Ыстық ірімшікті пицца",
      ru: "Пицца порционная",
      en: "Personal cheese pizza"
    },
    descriptions: {
      kz: "Моцарелла ірімшігі, шұжық пен қызанақ соусы қосылған ыстық порциялық пицца.",
      ru: "Горячая сытная пицца с сыром моцарелла, колбасками и томатным соусом.",
      en: "Hot baked pizza slice with melted mozzarella, savory sausage, and tomato sauce."
    }
    image: "assets/menu/bk-05.jpg"
  },

  // --- Сусындар | Напитки | Drinks ---
  {
    id: "bar-dr-1",
    category: "drinks",
    priceDisplay: "1 500 / 1 700 ₸",
    price: 1500,
    volume: "1 / 0,4 л",
    names: {
      kz: "Түрлі жемісті лимонадтар",
      ru: "Лимонады в ассортименте",
      en: "Assorted fruit lemonades"
    },
    descriptions: {
      kz: "Жол бойында шөл басатын салқын gazды жеміс лимонады.",
      ru: "Освежающий газированный фруктовый лимонад со льдом и ярким вкусом.",
      en: "Chilled sparkling fruity lemonades with natural citrus zest."
    }
    image: "assets/menu/dr-01.jpg"
  },
  {
    id: "bar-dr-2",
    category: "drinks",
    price: 1500,
    volume: "1 л",
    names: {
      kz: "Табиғи жеміс шырындары",
      ru: "Соки натуральные в ассортименте",
      en: "Natural fruit juices"
    },
    descriptions: {
      kz: "Алма, апельсин немесе мультифрукт дәмі бар балғын табиғи шырындар.",
      ru: "Освежающий натуральный фруктовый сок (яблоко, апельсин, мультифрукт).",
      en: "Chilled pure fruit juices (apple, orange, mixed fruit)."
    }
    image: "assets/menu/dr-02.jpg"
  },
  {
    id: "bar-dr-3",
    category: "drinks",
    price: 700,
    volume: "0,2 л",
    names: {
      kz: "Түтікшелі балалар шырыны",
      ru: "Детский сок с трубочкой",
      en: "Kids juice box with straw"
    },
    descriptions: {
      kz: "Кішкентай жолаушыларға арналған ыңғайлы түтікшесі бар табиғи шырын.",
      ru: "Удобная коробочка натурального сока для маленьких путешественников.",
      en: "Convenient natural juice box designed for young passengers."
    }
    image: "assets/menu/dr-03.jpg"
  },
  {
    id: "bar-dr-4",
    category: "drinks",
    price: 700,
    volume: "1,5 л",
    names: {
      kz: "Сарыағаш минералды суы",
      ru: "Минеральная вода Сарыагаш",
      en: "Saryagash mineral water"
    },
    descriptions: {
      kz: "Қазақстанның әйгілі табиғи минералды емдік-асханалық газдалған суы.",
      ru: "Знаменитая природная минеральная лечебно-столовая вода из Казахстана.",
      en: "Renowned Kazakhstan natural sparkling mineral water."
    }
    image: "assets/menu/dr-04.jpg"
  },
  {
    id: "bar-dr-5",
    category: "drinks",
    priceDisplay: "1 000 / 650 ₸",
    price: 650,
    volume: "1 / 0,5 л",
    names: {
      kz: "Кока-кола салқын сусыны",
      ru: "Coca-Cola (газ. напиток)",
      en: "Coca-Cola chilled drink"
    },
    descriptions: {
      kz: "Мұздай сергітетін әйгілі классикалық Coca-Cola газды сусыны.",
      ru: "Классический охлажденный газированный напиток Coca-Cola.",
      en: "Chilled iconic refreshing Coca-Cola soda."
    }
    image: "assets/menu/dr-05.jpg"
  },
  {
    id: "bar-dr-6",
    category: "drinks",
    priceDisplay: "1 000 / 650 ₸",
    price: 650,
    volume: "1 / 0,5 л",
    names: {
      kz: "Макси чай / Fuse Tea салқын шайы",
      ru: "Maxi Tea / Fuse Tea холодный чай",
      en: "Maxi Tea / Fuse Tea iced tea"
    },
    descriptions: {
      kz: "Шабдалы немесе лимон дәмі бар сергіткіш салқын шөл басар шай.",
      ru: "Освежающий холодный чай с сочным вкусом персика или лимона.",
      en: "Refreshing chilled iced tea with peach or lemon infusion."
    }
    image: "assets/menu/dr-06.jpg"
  },
  {
    id: "bar-dr-7",
    category: "drinks",
    priceDisplay: "700 / 500 ₸",
    price: 500,
    volume: "1 / 0,5 л",
    names: {
      kz: "Табиғи газдалмаған ауыз су",
      ru: "Вода питьевая негазированная",
      en: "Pure still drinking water"
    },
    descriptions: {
      kz: "Мөлдір таза табиғи газдалмаған бөтелкедегі ауыз суы.",
      ru: "Кристально чистая природная питьевая вода без газа.",
      en: "Pure natural still drinking water bottle."
    }
    image: "assets/menu/dr-07.jpg"
  },
  {
    id: "bar-dr-8",
    category: "drinks",
    price: 900,
    volume: "0,33 л",
    names: {
      kz: "Диззи энергетикалық сусыны",
      ru: "Dizzy энергетический напиток",
      en: "Dizzy energy drink"
    },
    descriptions: {
      kz: "Ұзақ сапарда сергектік пен күш-қуат беретін салқын энергетикалық сусын.",
      ru: "Бодрящий энергетический напиток для поддержания сил во время долгой поездки.",
      en: "Chilled energy drink to keep your energy high during night travels."
    }
    image: "assets/menu/dr-08.jpg"
  },
  {
    id: "bar-dr-9",
    category: "drinks",
    price: 1000,
    volume: "0,5 л",
    names: {
      kz: "Горилла энергетикалық сусыны",
      ru: "Gorilla энергетический напиток",
      en: "Gorilla energy drink"
    },
    descriptions: {
      kz: "Қуаттандыратын ерекше дәмі бар салқын Gorilla энергетикалық сусыны.",
      ru: "Мощный энергетический напиток для максимального заряда бодрости.",
      en: "Powerful energy drink for a quick refreshing boost."
    }
    image: "assets/menu/dr-09.jpg"
  },

  // --- Арақ | Водка | Vodka ---
  {
    id: "bar-v-1",
    category: "vodka",
    price: 6000,
    volume: "0,5 л",
    names: {
      kz: "Хаома",
      ru: "Хаома",
      en: "Haoma"
    }
  },
  {
    id: "bar-v-2",
    category: "vodka",
    price: 6000,
    volume: "0,5 л",
    names: {
      kz: "Зерно",
      ru: "Зерно",
      en: "Zerno"
    }
  },
  {
    id: "bar-v-3",
    category: "vodka",
    price: 7000,
    volume: "0,5 л",
    names: {
      kz: "Organic",
      ru: "Organic",
      en: "Organic"
    }
  },
  {
    id: "bar-v-4",
    category: "vodka",
    price: 7000,
    volume: "0,5 л",
    names: {
      kz: "Хортица айс",
      ru: "Хортица айс",
      en: "Khortytsa ice"
    }
  },
  {
    id: "bar-v-5",
    category: "vodka",
    price: 7000,
    volume: "0,5 л",
    names: {
      kz: "Кызылжар",
      ru: "Кызылжар",
      en: "Kyzylzhar"
    }
  },
  {
    id: "bar-v-6",
    category: "vodka",
    price: 9000,
    volume: "0,5 л",
    names: {
      kz: "Nemiroff Lex",
      ru: "Nemiroff Lex",
      en: "Nemiroff Lex"
    }
  },

  // --- Коньяк, Шарап, Виски | Cognac, Wine, Whisky ---
  {
    id: "bar-alc-1",
    category: "spirits",
    priceDisplay: "700 / 7 000 ₸",
    price: 700,
    volume: "0,50 / 0,5 л",
    names: {
      kz: "Қазақстан ескірген коньяғы",
      ru: "Коньяк Казахстан выдержанный",
      en: "Kazakhstan aged amber cognac"
    },
    descriptions: {
      kz: "Емен бөшкесінде бапталған ваниль мен кепкен жеміс хош иісі бар атақты коньяк.",
      ru: "Благородный золотисто-янтарный коньяк из отборных виноматериалов с тонами ванили и дуба.",
      en: "Aged golden amber brandy with smooth notes of oak, vanilla, and dried fruits."
    }
    image: "assets/menu/sp-01.jpg"
  },
  {
    id: "bar-alc-2",
    category: "spirits",
    price: 7000,
    volume: "0,7 л",
    names: {
      kz: "Коллекциялық шарап (қызыл / ақ)",
      ru: "Вино коллекционное (красное / белое)",
      en: "Fine wine bottle (red / white)"
    },
    descriptions: {
      kz: "Жемісті үйлесімді хош иісі бар таңдаулы қызыл немесе ақ шарап бөтелкесі.",
      ru: "Изысканное столовое вино с гармоничным фруктовым букетом и долгим послевкусием.",
      en: "Selected dining wine featuring balanced fruit bouquet and elegant finish."
    }
    image: "assets/menu/sp-02.jpg"
  },
  {
    id: "bar-alc-3",
    category: "spirits",
    priceDisplay: "1 500 / 15 000 ₸",
    price: 1500,
    volume: "0,50 / 0,5 л",
    names: {
      kz: "Ballantines шотланд вискиі",
      ru: "Виски Ballantine's Scotch",
      en: "Ballantine's Blended Scotch Whisky"
    },
    descriptions: {
      kz: "Бал мен піскен алманың үйлесімді дәмі бар әйгілі купажды шотланд вискиі.",
      ru: "Знаменитый купажированный шотландский виски со сбалансированным вкусом меда и спелых яблок.",
      en: "Renowned blended Scotch whisky balanced with subtle notes of honey, vanilla, and apple."
    }
    image: "assets/menu/sp-03.jpg"
  },
  {
    id: "bar-alc-4",
    category: "spirits",
    priceDisplay: "2 000 / 20 000 ₸",
    price: 2000,
    volume: "0,50 / 0,5 л",
    names: {
      kz: "Jack Daniel's америкалық вискиі",
      ru: "Виски Jack Daniel's Tennessee",
      en: "Jack Daniel's Tennessee Whiskey"
    },
    descriptions: {
      kz: "Қантты үйеңкі көмірінен сүзілген карамель мен түтін дәмі бар аңызға айналған виски.",
      ru: "Легендарный американский виски с фильтрацией через уголь сахарного клена и нотками карамели.",
      en: "Iconic charcoal-mellowed Tennessee whiskey with rich caramel and toasted oak aroma."
    }
    image: "assets/menu/sp-04.jpg"
  },

  // --- Сыра | Пиво | Beer ---
  {
    id: "bar-beer-1",
    category: "beer",
    price: 1200,
    volume: "0,45 л",
    names: {
      kz: "Балғын құйма сыра кружкасы",
      ru: "Кружка свежего разливного пива",
      en: "Mug of fresh draft beer"
    },
    descriptions: {
      kz: "Қою ақ көбігі бар, шөлді керемет басатын салқын құйма сыра.",
      ru: "Освежающее светлое разливное пиво с плотной белой шапкой пены.",
      en: "Chilled fresh draft lager served in a frosted mug with a creamy head."
    }
    image: "assets/menu/br-01.jpg"
  },
  {
    id: "bar-beer-2",
    category: "beer",
    price: 1200,
    volume: "0,45 л",
    names: {
      kz: "Ақ аю сырасы (Белый медведь)",
      ru: "Пиво Белый медведь",
      en: "Bely Medved lager beer"
    },
    descriptions: {
      kz: "Жұмсақ уыт дәмі мен жеңіл ащылығы бар классикалық ақшыл лагер.",
      ru: "Классический светлый лагер с мягким солодовым вкусом и легкой горчинкой.",
      en: "Classic light lager with mellow malt flavor and clean crisp finish."
    }
    image: "assets/menu/br-02.jpg"
  },
  {
    id: "bar-beer-3",
    category: "beer",
    price: 1200,
    volume: "0,45 л",
    names: {
      kz: "Жатецкий гусь чех сырасы",
      ru: "Пиво Жатецкий гусь",
      en: "Zatecky Gus Czech-style beer"
    },
    descriptions: {
      kz: "Атақты чех жатец құлмағынан қайнатылған хош иісті сыра.",
      ru: "Традиционное пиво, сваренное с добавлением знаменитого чешского жатецкого хмеля.",
      en: "Aromatic lager brewed with celebrated Saaz hops for rich herbal flavor."
    }
    image: "assets/menu/br-03.jpg"
  },
  {
    id: "bar-beer-4",
    category: "beer",
    price: 1200,
    volume: "0,45 л",
    names: {
      kz: "Жигули дәстүрлі сырасы",
      ru: "Пиво Жигулевское",
      en: "Zhigulevskoe classic beer"
    },
    descriptions: {
      kz: "Таза арпа уыты дәмі бар әйгілі дәстүрлі ақшыл сыра сорты.",
      ru: "Легендарный советский сорт светлого ячменного пива с чистым вкусом.",
      en: "Legendary crisp pale lager brewed to authentic heritage standards."
    }
    image: "assets/menu/br-04.jpg"
  },
  {
    id: "bar-beer-5",
    category: "beer",
    price: 1200,
    volume: "0,45 л",
    names: {
      kz: "Прага премиум сырасы",
      ru: "Пиво Прага (Praga)",
      en: "Praga premium pilsner"
    },
    descriptions: {
      kz: "Алтын түстес реңкі және ерекше дәмі бар еуропалық премиум сыра.",
      ru: "Премиальный европейский пилснер с глубоким золотистым цветом и благородным хмелем.",
      en: "European premium pilsner with deep golden hue and noble hop bitterness."
    }
    image: "assets/menu/br-05.jpg"
  },
  {
    id: "bar-beer-6",
    category: "beer",
    price: 1500,
    volume: "0,5 л",
    names: {
      kz: "Miller салқын сырасы",
      ru: "Пиво Miller Genuine Draft",
      en: "Miller Genuine Draft beer"
    },
    descriptions: {
      kz: "Төрт мәрте салқын сүзгіден өткен жұмсақ дәмі бар америкалық сыра.",
      ru: "Мягкое американское пиво четырехкратной холодной фильтрации в прозрачной бутылке.",
      en: "Exceptionally smooth cold-filtered American draft lager in bottle."
    }
    image: "assets/menu/br-06.jpg"
  },
  {
    id: "bar-beer-7",
    category: "beer",
    price: 1500,
    volume: "0,5 л",
    names: {
      kz: "Heineken премиум сырасы",
      ru: "Пиво Heineken премиум",
      en: "Heineken premium lager"
    },
    descriptions: {
      kz: "Әлемге танымал голландиялық премиум ақшыл лагер сырасы.",
      ru: "Всемирно известный премиальный нидерландский лагер в фирменной зеленой бутылке.",
      en: "World-famous Dutch premium lager with characteristic 100% barley malt."
    }
    image: "assets/menu/br-07.jpg"
  },

  // --- Сыраға | К пиву | For beer (Snacks) ---
  {
    id: "bar-snack-1",
    category: "beer-snacks",
    priceDisplay: "1 000 / 700 ₸",
    price: 700,
    volume: "80 / 40 гр",
    names: {
      kz: "Lays қытырлақ картоп чипсылары",
      ru: "Чипсы Lay's в ассортименте",
      en: "Lay's potato chips assortment"
    },
    descriptions: {
      kz: "Табиғи картоптан әзірленген қытырлақ Lays чипсыларының ассортименті.",
      ru: "Хрустящие картофельные чипсы из натурального картофеля с любимыми вкусами.",
      en: "Crispy salted potato chips made with natural potatoes in popular flavors."
    }
    image: "assets/menu/bs-01.jpg"
  },
  {
    id: "bar-snack-2",
    category: "beer-snacks",
    priceDisplay: "800 / 500 ₸",
    price: 500,
    volume: "130 / 40 гр",
    names: {
      kz: "Кептірілген қытырлақ нан (сухарики)",
      ru: "Сухарики ржаные к пиву",
      en: "Toasted rye beer croutons"
    },
    descriptions: {
      kz: "Сарымсақ немесе қақталған дәмдеуіштер қосылған қытырлақ қара нан.",
      ru: "Пикантные хрустящие ржаные сухарики с чесноком или вкусом дымка.",
      en: "Crunchy roasted rye bread croutons seasoned with garlic and spices."
    }
    image: "assets/menu/bs-02.jpg"
  },
  {
    id: "bar-snack-3",
    category: "beer-snacks",
    price: 800,
    volume: "50 гр",
    names: {
      kz: "Қуырылған тұзды жержаңғақ",
      ru: "Арахис соленый обжаренный",
      en: "Roasted salted peanuts"
    },
    descriptions: {
      kz: "Теңіз тұзымен алтын түстес қызарып қуырылған таңдаулы жержаңғақ.",
      ru: "Золотистый отборный обжаренный арахис с морской солью.",
      en: "Golden crunchy peanuts roasted with fine sea salt."
    }
    image: "assets/menu/bs-03.jpg"
  },
  {
    id: "bar-snack-4",
    category: "beer-snacks",
    price: 800,
    volume: "30 гр",
    names: {
      kz: "Таңдаулы тұздалған пісте (фисташки)",
      ru: "Фисташки отборные соленые",
      en: "Premium salted pistachios"
    },
    descriptions: {
      kz: "Жеңіл тұздалған, қабығы ашылған ірі әрі сапалы дәмді пісте.",
      ru: "Отборные калифорнийские фисташки в раскрытой скорлупе с легкой солью.",
      en: "Roasted jumbo in-shell pistachios with light sea salt."
    }
    image: "assets/menu/bs-04.jpg"
  },
  {
    id: "bar-snack-5",
    category: "beer-snacks",
    price: 800,
    volume: "50 гр",
    names: {
      kz: "Чечил қақталған сүзбе ірімшігі",
      ru: "Сыр Чечил копченый косичка",
      en: "Chechil smoked string cheese"
    },
    descriptions: {
      kz: "Салқын сыра мен сусындарға өте үйлесімді қақталған өрімді Чечил ірімшігі.",
      ru: "Традиционный натуральный копченый волокнистый сыр к прохладным напиткам.",
      en: "Braided smoked string cheese with savory smoky aroma and chewy texture."
    }
    image: "assets/menu/bs-05.jpg"
  }
];

// ==========================================
// 3. UI TRANSLATIONS DICTIONARY (KZ | RU | EN)
// ==========================================
const I18N = {
  kz: {
    nav: {
      home: "Басты бет",
      menu: "Мәзір",
      lunchboxes: "Ланчбокстар",
      bar: "Бар",
      about: "Біз туралы",
      gallery: "Галерея",
      contacts: "Байланыс",
      bookBtn: "ҮСТЕЛ БРОНДАУ"
    },
    hero: {
      brandSub: "DAR | RES group",
      title: "Қайта оралғыңыз келетін дәм",
      subtitle: "Таңғы ас, дәстүрлі тағамдар, әлем асханасы және жайлы атмосфера.",
      btnMenu: "МӘЗІРДІ КӨРУ",
      btnBook: "ҮСТЕЛ БРОНДАУ",
      badge1: "100% Халал сапа",
      badge2: "Шынайы дәстүр",
      badge3: "Жайлы қонақжайлық"
    },
    sections: {
      menuTitle: "Мейрамхана мәзірі",
      menuSubtitle: "Дәстүрлі рецепттер мен авторлық дәмдердің үйлесімі",
      barTitle: "Бар мәзірі",
      barSubtitle: "Ыстық шайлар, сергітетін сусындар және таңдаулы сусындар топтамасы",
      aboutTitle: "DAR | RES group",
      aboutSubtitle: "Біз туралы",
      galleryTitle: "Фотогалерея",
      gallerySubtitle: "Біздің атмосфера мен дәмді сәттер",
      bookingTitle: "Үстел брондау",
      bookingSubtitle: "Алдын ала орын алып, сапалы демалыстан ләззат алыңыз",
      contactsTitle: "Байланыс",
      contactsSubtitle: "Бізге келіңіз немесе хабарласыңыз"
    },
    menuCategories: {
      all: "Барлық тағамдар",
      breakfast: "Таңғы ас",
      appetizers: "Салқын тағамдар",
      "first-courses": "Бірінші тамақ",
      salads: "Салаттар",
      "main-courses": "Негізгі тағамдар",
      "side-dishes": "Гарнирлер"
    },
    barCategories: {
      all: "Барлық бар",
      "hot-drinks": "Ыстық сусындар",
      "for-tea": "Шайға",
      bakery: "Нан өнімдері",
      drinks: "Сусындар",
      vodka: "Арақ",
      spirits: "Коньяк / Шарап / Виски",
      beer: "Сыра",
      "beer-snacks": "Сыраға"
    },
    serviceCharge: "Қызмет 10% | Обслуживание 10% | Service 10%",
    searchPlaceholder: "Тағам немесе ингредиент бойынша іздеу...",
    dishNotFound: "Бұл санатта ештеңе табылмады",
    aboutText: "«Дәстүрлі тағамдар, заманауи тағамдар және қонақжай атмосфера есте қаларлық таңғы астар, түскі астар, кешкі астар мен кездесулер үшін бірігетін орын.»",
    bookingForm: {
      name: "Аты-жөніңіз",
      namePlaceholder: "Мысалы: Арман",
      phone: "Телефон нөмірі",
      phonePlaceholder: "+7 (7XX) XXX-XX-XX",
      date: "Күні",
      time: "Уақыты",
      guests: "Қонақтар саны",
      guestsPlaceholder: "2 адам",
      comment: "Қосымша тілек",
      commentPlaceholder: "Үстелге қойылатын талаптар немесе ерекше тілектер...",
      submitBtn: "ӨТІНІШТІ ЖІБЕРУ",
      successMsg: "Рахмет! Сіздің брондау өтінішіңіз қабылданды. Біз сізбен брондауды растау үшін байланысамыз."
    },
    contacts: {
      addressLabel: "Мекенжайы",
      addressValue: "Қазақстан, [Мейрамхана мекенжайы осында көрсетіледі]",
      phoneLabel: "Телефон",
      phoneValue: "+7 (7XX) XXX-XX-XX",
      whatsappLabel: "WhatsApp",
      whatsappValue: "+7 (7XX) XXX-XX-XX",
      instagramLabel: "Instagram",
      instagramValue: "@dar_res_group",
      hoursLabel: "Жұмыс кестесі",
      hoursValue: "Дүйсенбі – Жексенбі: 08:00 – 00:00",
      btnCall: "ҚОҢЫРАУ ШАЛУ",
      btnWhatsapp: "WHATSAPP",
      btnDirections: "МАРШРУТТЫ КӨРСЕТУ"
    },
    footer: {
      rights: "© 2026 DAR | RES group. Барлық құқықтар қорғалған.",
      tagline: "DAR | RES group — Пойыздардағы жолаушыларға арналған ресторандық тағамдар мен сусындар сервисі."
    },
    qrBadge: "📱 Үстелден онлайн мәзір (QR)",
    closeModal: "Жабу"
  },

  ru: {
    nav: {
      home: "Главная",
      menu: "Меню",
      lunchboxes: "Ланчбоксы",
      bar: "Бар",
      about: "О нас",
      gallery: "Галерея",
      contacts: "Контакты",
      bookBtn: "ЗАБРОНИРОВАТЬ СТОЛ"
    },
    hero: {
      brandSub: "DAR | RES group",
      title: "A Taste You’ll Want to Come Back To",
      subtitle: "Breakfast, traditional dishes, international cuisine, and a welcoming atmosphere.",
      btnMenu: "ПОСМОТРЕТЬ МЕНЮ",
      btnBook: "ЗАБРОНИРОВАТЬ СТОЛ",
      badge1: "100% Халал качество",
      badge2: "Аутентичные рецепты",
      badge3: "Уютная атмосфера"
    },
    sections: {
      menuTitle: "Меню ресторана",
      menuSubtitle: "Изысканные блюда, приготовленные из отборных свежих ингредиентов",
      barTitle: "Барное меню",
      barSubtitle: "Горячий чай, освежающие лимонады и богатая барная карта",
      aboutTitle: "DAR | RES group",
      aboutSubtitle: "О нас",
      galleryTitle: "Фотогалерея",
      gallerySubtitle: "Атмосфера ресторана, интерьер и авторские подачи",
      bookingTitle: "Забронировать стол",
      bookingSubtitle: "Запланируйте ваш визит заранее и проведите время с комфортом",
      contactsTitle: "Контакты",
      contactsSubtitle: "Мы всегда рады видеть вас в гостях"
    },
    menuCategories: {
      all: "Все блюда",
      breakfast: "Завтраки",
      appetizers: "Холодные закуски",
      "first-courses": "Первые блюда",
      salads: "Салаты",
      "main-courses": "Вторые блюда",
      "side-dishes": "Гарниры"
    },
    barCategories: {
      all: "Всё меню бара",
      "hot-drinks": "Горячие напитки",
      "for-tea": "К чаю",
      bakery: "Выпечка",
      drinks: "Напитки",
      vodka: "Водка",
      spirits: "Коньяк / Вино / Виски",
      beer: "Пиво",
      "beer-snacks": "К пиву"
    },
    serviceCharge: "Қызмет 10% | Обслуживание 10% | Service 10%",
    searchPlaceholder: "Поиск блюда по названию или составу...",
    dishNotFound: "Блюда не найдены",
    aboutText: "«Место, где традиционные блюда, современная кухня и гостеприимная атмосфера объединяются для незабываемых завтраков, обедов, ужинов и встреч.»",
    bookingForm: {
      name: "Ваше имя",
      namePlaceholder: "Например: Азамат",
      phone: "Номер телефона",
      phonePlaceholder: "+7 (7XX) XXX-XX-XX",
      date: "Дата визита",
      time: "Время",
      guests: "Количество гостей",
      guestsPlaceholder: "2 персоны",
      comment: "Комментарий к брони",
      commentPlaceholder: "Пожелания по посадке или особые предпочтения...",
      submitBtn: "ОТПРАВИТЬ ЗАПРОС",
      successMsg: "Спасибо! Ваш запрос на бронирование отправлен. Мы свяжемся с вами для подтверждения брони."
    },
    contacts: {
      addressLabel: "Адрес",
      addressValue: "Казахстан, [Адрес ресторана будет указан здесь]",
      phoneLabel: "Телефон",
      phoneValue: "+7 (7XX) XXX-XX-XX",
      whatsappLabel: "WhatsApp",
      whatsappValue: "+7 (7XX) XXX-XX-XX",
      instagramLabel: "Instagram",
      instagramValue: "@dar_res_group",
      hoursLabel: "Режим работы",
      hoursValue: "Пн – Вс: 08:00 – 00:00",
      btnCall: "ПОЗВОНИТЬ",
      btnWhatsapp: "WHATSAPP",
      btnDirections: "КАК ДОБРАТЬСЯ"
    },
    footer: {
      rights: "© 2026 DAR | RES group. Все права защищены.",
      tagline: "DAR | RES group — Сервис ресторанного питания и напитков для пассажиров поездов."
    },
    qrBadge: "📱 Быстрое цифровое меню для столов (QR)",
    closeModal: "Закрыть"
  },

  en: {
    nav: {
      home: "Home",
      menu: "Menu",
      lunchboxes: "Lunchboxes",
      bar: "Bar",
      about: "About Us",
      gallery: "Gallery",
      contacts: "Contacts",
      bookBtn: "BOOK A TABLE"
    },
    hero: {
      brandSub: "DAR | RES group",
      title: "A Taste You’ll Want to Come Back To",
      subtitle: "Breakfast, traditional dishes, international cuisine, and a welcoming atmosphere.",
      btnMenu: "VIEW MENU",
      btnBook: "BOOK A TABLE",
      badge1: "100% Halal Quality",
      badge2: "Authentic Recipes",
      badge3: "Warm Hospitality"
    },
    sections: {
      menuTitle: "Restaurant Menu",
      menuSubtitle: "Exceptional culinary tradition made with pure fresh ingredients",
      barTitle: "Bar Menu",
      barSubtitle: "Aromatic artisanal teas, cold beverages, and curated cellar collection",
      aboutTitle: "DAR | RES group",
      aboutSubtitle: "About Us",
      galleryTitle: "Photo Gallery",
      gallerySubtitle: "Atmospheric spaces, dining moments and culinary craftsmanship",
      bookingTitle: "Book a Table",
      bookingSubtitle: "Reserve your memorable dining experience in advance",
      contactsTitle: "Contacts",
      contactsSubtitle: "We look forward to welcoming you"
    },
    menuCategories: {
      all: "All dishes",
      breakfast: "Breakfast",
      appetizers: "Appetizers",
      "first-courses": "First Courses",
      salads: "Salads",
      "main-courses": "Main Courses",
      "side-dishes": "Side Dishes"
    },
    barCategories: {
      all: "All Bar Items",
      "hot-drinks": "Hot Drinks",
      "for-tea": "For Tea",
      bakery: "Bakery Products",
      drinks: "Drinks",
      vodka: "Vodka",
      spirits: "Cognac / Wine / Whisky",
      beer: "Beer",
      "beer-snacks": "Beer Snacks"
    },
    serviceCharge: "Қызмет 10% | Обслуживание 10% | Service 10%",
    searchPlaceholder: "Search dishes by name or ingredients...",
    dishNotFound: "No dishes found in this category",
    aboutText: "“A place where traditional dishes, modern cuisine, and a welcoming atmosphere come together for memorable breakfasts, lunches, dinners, and meetings.”",
    bookingForm: {
      name: "Your Name",
      namePlaceholder: "e.g. Alex",
      phone: "Phone Number",
      phonePlaceholder: "+7 (7XX) XXX-XX-XX",
      date: "Date",
      time: "Time",
      guests: "Number of Guests",
      guestsPlaceholder: "2 guests",
      comment: "Special requests",
      commentPlaceholder: "Table seating preference or dietary notes...",
      submitBtn: "SEND REQUEST",
      successMsg: "Thank you! Your booking request has been sent. We will contact you to confirm your reservation."
    },
    contacts: {
      addressLabel: "Address",
      addressValue: "Kazakhstan, [Restaurant address placeholder]",
      phoneLabel: "Phone Number",
      phoneValue: "+7 (7XX) XXX-XX-XX",
      whatsappLabel: "WhatsApp",
      whatsappValue: "+7 (7XX) XXX-XX-XX",
      instagramLabel: "Instagram",
      instagramValue: "@dar_res_group",
      hoursLabel: "Opening Hours",
      hoursValue: "Mon – Sun: 08:00 – 00:00",
      btnCall: "CALL",
      btnWhatsapp: "WHATSAPP",
      btnDirections: "GET DIRECTIONS"
    },
    footer: {
      rights: "© 2026 DAR | RES group. All rights reserved.",
      tagline: "DAR | RES group — Restaurant food and beverage service for train passengers."
    },
    qrBadge: "📱 Digital Table QR Menu",
    closeModal: "Close"
  }
};
I18N.kk = I18N.kz;

// ==========================================
// 4. APPLICATION STATE & CONTROLLER
// ==========================================
let currentLang = localStorage.getItem("dar_res_lang") || "ru";
let currentMenuCategory = "all";
let currentBarCategory = "all";
let currentMenuSearch = "";
let currentGalleryFilter = "all";

// Formatting utility for Kazakhstan Tenge
function formatCurrency(amount) {
  return new Intl.NumberFormat("ru-RU").format(amount) + " ₸";
}

// Language Switcher Function
function setLanguage(lang) {
  if (!I18N[lang]) lang = "ru";
  currentLang = lang;
  localStorage.setItem("dar_res_lang", lang); localStorage.setItem("dar_res_passenger_lang", lang);

  // Update active pill in header and mobile drawer
  document.querySelectorAll(".lang-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.lang === lang);
  });

  // Apply translations to static data-i18n elements
  applyTranslations();

  // Re-render dynamic lists with new language names
  renderRestaurantCategories();
  renderRestaurantMenu();
  renderBarCategories();
  renderBarMenu();
}

// Apply static text updates
function applyTranslations() {
  const dict = I18N[currentLang];

  // Navigation
  document.querySelectorAll("[data-i18n-nav]").forEach(el => {
    const key = el.dataset.i18nNav;
    if (dict.nav[key]) el.textContent = dict.nav[key];
  });

  // Hero
  document.querySelectorAll("[data-i18n-hero]").forEach(el => {
    const key = el.dataset.i18nHero;
    if (dict.hero[key]) el.textContent = dict.hero[key];
  });

  // Section titles
  document.querySelectorAll("[data-i18n-sec]").forEach(el => {
    const key = el.dataset.i18nSec;
    if (dict.sections[key]) el.textContent = dict.sections[key];
  });

  // Service charges
  document.querySelectorAll(".service-charge-banner span").forEach(el => {
    el.textContent = dict.serviceCharge;
  });

  // Search input
  const searchInput = document.getElementById("menuSearchInput");
  if (searchInput) {
    searchInput.placeholder = dict.searchPlaceholder;
  }

  // About text
  const aboutQuote = document.getElementById("aboutBrandQuote");
  if (aboutQuote) {
    aboutQuote.textContent = dict.aboutText;
  }

  // Booking labels and placeholders
  document.querySelectorAll("[data-i18n-booking]").forEach(el => {
    const key = el.dataset.i18nBooking;
    if (dict.bookingForm[key]) {
      if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
        el.placeholder = dict.bookingForm[key];
      } else {
        el.textContent = dict.bookingForm[key];
      }
    }
  });

  // Contacts
  document.querySelectorAll("[data-i18n-contact]").forEach(el => {
    const key = el.dataset.i18nContact;
    if (dict.contacts[key]) el.textContent = dict.contacts[key];
  });

  // Footer
  document.querySelectorAll("[data-i18n-footer]").forEach(el => {
    const key = el.dataset.i18nFooter;
    if (dict.footer[key]) el.textContent = dict.footer[key];
  });

  // QR Mode Badge
  const qrBadgeEl = document.getElementById("qrModeIndicator");
  if (qrBadgeEl) {
    qrBadgeEl.textContent = dict.qrBadge;
  }
}

// Render Category Tabs for Restaurant Menu
function renderRestaurantCategories() {
  const container = document.getElementById("restaurantCategoryTabs");
  if (!container) return;

  const categories = [
    { key: "all", label: I18N[currentLang].menuCategories.all },
    { key: "breakfast", label: I18N[currentLang].menuCategories.breakfast },
    { key: "appetizers", label: I18N[currentLang].menuCategories.appetizers },
    { key: "first-courses", label: I18N[currentLang].menuCategories["first-courses"] },
    { key: "salads", label: I18N[currentLang].menuCategories.salads },
    { key: "main-courses", label: I18N[currentLang].menuCategories["main-courses"] },
    { key: "side-dishes", label: I18N[currentLang].menuCategories["side-dishes"] }
  ];

  container.innerHTML = categories.map(cat => `
    <button 
      class="cat-tab-btn ${cat.key === currentMenuCategory ? 'active' : ''}" 
      data-cat="${cat.key}"
      aria-pressed="${cat.key === currentMenuCategory}"
    >
      ${cat.label}
    </button>
  `).join("");

  container.querySelectorAll(".cat-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      currentMenuCategory = btn.dataset.cat;
      renderRestaurantCategories();
      renderRestaurantMenu();
    });
  });
}

// Render Food Menu Cards
function renderRestaurantMenu() {
  const container = document.getElementById("restaurantMenuGrid");
  if (!container) return;

  const filtered = RESTAURANT_MENU_DATA.filter(item => {
    const matchesCat = currentMenuCategory === "all" || item.category === currentMenuCategory;
    if (!matchesCat) return false;

    if (!currentMenuSearch) return true;
    const q = currentMenuSearch.toLowerCase();
    const nameMatch = (item.names.ru && item.names.ru.toLowerCase().includes(q)) ||
                      (item.names.kz && item.names.kz.toLowerCase().includes(q)) ||
                      (item.names.en && item.names.en.toLowerCase().includes(q));
    const descMatch = (item.descriptions.ru && item.descriptions.ru.toLowerCase().includes(q)) ||
                      (item.descriptions.kz && item.descriptions.kz.toLowerCase().includes(q)) ||
                      (item.descriptions.en && item.descriptions.en.toLowerCase().includes(q));
    return nameMatch || descMatch;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="menu-empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#888580" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <p>${I18N[currentLang].dishNotFound}</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(item => {
    const primaryName = item.names[currentLang] || item.names.ru;
    // Provide bilingual secondary subtitle (Kazakh / Russian / English as per example requirement)
    let secondaryNames = [];
    if (currentLang === "ru") {
      if (item.names.kz && item.names.kz !== primaryName) secondaryNames.push(item.names.kz);
      if (item.names.en && item.names.en !== primaryName) secondaryNames.push(item.names.en);
    } else if (currentLang === "kz") {
      if (item.names.ru && item.names.ru !== primaryName) secondaryNames.push(item.names.ru);
      if (item.names.en && item.names.en !== primaryName) secondaryNames.push(item.names.en);
    } else {
      if (item.names.ru && item.names.ru !== primaryName) secondaryNames.push(item.names.ru);
      if (item.names.kz && item.names.kz !== primaryName) secondaryNames.push(item.names.kz);
    }
    const secondaryStr = secondaryNames.filter(Boolean).join(" • ");
    const desc = item.descriptions[currentLang] || item.descriptions.ru || "";

    const hasImage = Boolean(item.image);

    const imgSrc = item.image || 'assets/menu/placeholder_food.jpg';
    return `
      <article class="menu-card has-img">
        <div class="menu-card-img-wrap">
          <img src="${imgSrc}" alt="${primaryName}" loading="lazy" onerror="this.onerror=null;this.src='assets/menu/placeholder_food.jpg';" />
        </div>
        <div class="menu-card-content">
          <div class="menu-card-header">
            <h3 class="dish-title">${primaryName}</h3>
            <span class="dish-price">${formatCurrency(item.price)}</span>
          </div>
          ${secondaryStr ? `<p class="dish-subtitles">${secondaryStr}</p>` : ''}
          ${desc ? `<p class="dish-desc">${desc}</p>` : ''}
          <div class="dish-meta">
            <span class="dish-weight">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
              ${item.weight}
            </span>
          </div>
        </div>
      </article>
    `;
  }).join("");
}

// Render Bar Categories
function renderBarCategories() {
  const container = document.getElementById("barCategoryTabs");
  if (!container) return;

  const categories = [
    { key: "all", label: I18N[currentLang].barCategories.all },
    { key: "hot-drinks", label: I18N[currentLang].barCategories["hot-drinks"] },
    { key: "for-tea", label: I18N[currentLang].barCategories["for-tea"] },
    { key: "bakery", label: I18N[currentLang].barCategories.bakery },
    { key: "drinks", label: I18N[currentLang].barCategories.drinks },
    { key: "vodka", label: I18N[currentLang].barCategories.vodka },
    { key: "spirits", label: I18N[currentLang].barCategories.spirits },
    { key: "beer", label: I18N[currentLang].barCategories.beer },
    { key: "beer-snacks", label: I18N[currentLang].barCategories["beer-snacks"] }
  ];

  container.innerHTML = categories.map(cat => `
    <button 
      class="cat-tab-btn ${cat.key === currentBarCategory ? 'active' : ''}" 
      data-bar-cat="${cat.key}"
    >
      ${cat.label}
    </button>
  `).join("");

  container.querySelectorAll(".cat-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      currentBarCategory = btn.dataset.barCat;
      renderBarCategories();
      renderBarMenu();
    });
  });
}

// Render Bar Menu Cards
function renderBarMenu() {
  const container = document.getElementById("barMenuGrid");
  if (!container) return;

  const filtered = BAR_MENU_DATA.filter(item => {
    return currentBarCategory === "all" || item.category === currentBarCategory;
  });

  container.innerHTML = filtered.map(item => {
    const primaryName = item.names[currentLang] || item.names.ru;
    // Show other language name if available
    let altName = "";
    if (currentLang === "ru" && item.names.kz && item.names.kz !== primaryName) {
      altName = item.names.kz;
    } else if (currentLang === "kz" && item.names.ru && item.names.ru !== primaryName) {
      altName = item.names.ru;
    } else if (currentLang === "en" && item.names.ru && item.names.ru !== primaryName) {
      altName = item.names.ru;
    }

    const priceText = item.priceDisplay || formatCurrency(item.price);

    const barImg = item.image || 'assets/menu/placeholder_food.jpg';
    return `
      <article class="bar-card">
        <div class="bar-card-img-wrap">
          <img src="${barImg}" alt="${primaryName}" loading="lazy" onerror="this.onerror=null;this.src='assets/menu/placeholder_food.jpg';" />
        </div>
        <div class="bar-card-main">
          <div class="bar-info">
            <h4 class="bar-title">${primaryName}</h4>
            ${altName ? `<span class="bar-alt">${altName}</span>` : ''}
          </div>
          <div class="bar-pricing">
            <span class="bar-vol">${item.volume}</span>
            <span class="bar-price">${priceText}</span>
          </div>
        </div>
      </article>
    `;
  }).join("");
}

// ==========================================
// 5. GALLERY & FULLSCREEN LIGHTBOX
// ==========================================
const GALLERY_ITEMS = [
  {
    src: "assets/hero_ambience.jpg",
    category: "interior",
    title: { ru: "Интерьер главного зала", kz: "Басты зал интерьері", en: "Main Dining Hall Interior" }
  },
  {
    src: "assets/food_plov.jpg",
    category: "food",
    title: { ru: "Традиционный восточный плов", kz: "Дәстүрлі шығыс палауы", en: "Traditional Festive Pilaf" }
  },
  {
    src: "assets/drinks_tea.jpg",
    category: "drinks",
    title: { ru: "Ташкентский чай и цитрусовый лимонад", kz: "Ташкент шайы мен цитрус лимонады", en: "Tashkent Tea & Craft Lemonade" }
  },
  {
    src: "assets/about_dining.jpg",
    category: "atmosphere",
    title: { ru: "Гостеприимная атмосфера вечера", kz: "Кешкі жайлы қонақжай атмосфера", en: "Evening Hospitality Atmosphere" }
  },
  {
    src: "assets/food_caesar.jpg",
    category: "food",
    title: { ru: "Салат Цезарь с куриным филе", kz: "Тауық еті қосылған цезарь салаты", en: "Caesar Salad with Tender Chicken" }
  },
  {
    src: "assets/food_breakfast.jpg",
    category: "breakfast",
    title: { ru: "Утренний фирменный завтрак", kz: "Таңғы авторлық ас", en: "Signature Morning Breakfast" }
  }
];

let activeLightboxIndex = 0;

function setupGallery() {
  const container = document.getElementById("galleryGrid");
  const filterBtns = document.querySelectorAll(".gallery-filter-btn");
  if (!container) return;

  function renderGallery() {
    const filtered = GALLERY_ITEMS.filter(item => {
      return currentGalleryFilter === "all" || item.category === currentGalleryFilter;
    });

    container.innerHTML = filtered.map((item, index) => {
      const title = item.title[currentLang] || item.title.ru;
      return `
        <div class="gallery-card" data-index="${index}">
          <img src="${item.src}" alt="${title}" loading="lazy" />
          <div class="gallery-card-overlay">
            <div class="gallery-card-meta">
              <span class="gallery-category">${item.category.toUpperCase()}</span>
              <h4 class="gallery-caption">${title}</h4>
            </div>
            <button class="gallery-zoom-btn" aria-label="Zoom image">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                <line x1="11" y1="8" x2="11" y2="14"></line>
                <line x1="8" y1="11" x2="14" y2="11"></line>
              </svg>
            </button>
          </div>
        </div>
      `;
    }).join("");

    container.querySelectorAll(".gallery-card").forEach(card => {
      card.addEventListener("click", () => {
        const idx = parseInt(card.dataset.index, 10);
        openLightbox(idx);
      });
    });
  }

  filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      filterBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentGalleryFilter = btn.dataset.filter;
      renderGallery();
    });
  });

  renderGallery();
}

function openLightbox(index) {
  activeLightboxIndex = index;
  const modal = document.getElementById("lightboxModal");
  const img = document.getElementById("lightboxImg");
  const caption = document.getElementById("lightboxCaption");
  if (!modal || !img) return;

  const item = GALLERY_ITEMS[activeLightboxIndex];
  img.src = item.src;
  caption.textContent = item.title[currentLang] || item.title.ru;
  modal.classList.add("open");
  document.body.style.overflow = "hidden";
}

function closeLightbox() {
  const modal = document.getElementById("lightboxModal");
  if (modal) {
    modal.classList.remove("open");
    document.body.style.overflow = "";
  }
}

function nextLightboxImage() {
  activeLightboxIndex = (activeLightboxIndex + 1) % GALLERY_ITEMS.length;
  openLightbox(activeLightboxIndex);
}

function prevLightboxImage() {
  activeLightboxIndex = (activeLightboxIndex - 1 + GALLERY_ITEMS.length) % GALLERY_ITEMS.length;
  openLightbox(activeLightboxIndex);
}

// ==========================================
// 6. BOOKING FORM HANDLER
// ==========================================
function setupBookingForm() {
  const form = document.getElementById("tableBookingForm");
  if (!form) return;

  // Set minimum date to today
  const dateInput = document.getElementById("bookDate");
  if (dateInput) {
    const today = new Date().toISOString().split("T")[0];
    dateInput.min = today;
    dateInput.value = today;
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const btn = form.querySelector("button[type='submit']");
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.innerHTML = `<span class="btn-spinner"></span>`;

    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = originalText;
      showBookingSuccessModal();
      form.reset();
      if (dateInput) {
        dateInput.value = new Date().toISOString().split("T")[0];
      }
    }, 700);
  });
}

function showBookingSuccessModal() {
  const modal = document.getElementById("bookingSuccessModal");
  const textEl = document.getElementById("bookingSuccessText");
  if (modal && textEl) {
    textEl.textContent = I18N[currentLang].bookingForm.successMsg;
    modal.classList.add("open");
  }
}

function closeBookingSuccessModal() {
  const modal = document.getElementById("bookingSuccessModal");
  if (modal) {
    modal.classList.remove("open");
  }
}

// ==========================================
// 7. MOBILE DRAWER & NAVIGATION
// ==========================================
function setupNavigation() {
  const hamburgerBtn = document.getElementById("mobileNavToggle");
  const drawer = document.getElementById("mobileDrawer");
  const overlay = document.getElementById("mobileOverlay");
  const closeBtn = document.getElementById("mobileDrawerClose");

  function openDrawer() {
    drawer.classList.add("open");
    overlay.classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function closeDrawer() {
    drawer.classList.remove("open");
    overlay.classList.remove("open");
    document.body.style.overflow = "";
  }

  if (hamburgerBtn) hamburgerBtn.addEventListener("click", openDrawer);
  if (closeBtn) closeBtn.addEventListener("click", closeDrawer);
  if (overlay) overlay.addEventListener("click", closeDrawer);

  document.querySelectorAll(".mobile-nav-link").forEach(link => {
    link.addEventListener("click", closeDrawer);
  });

  // Sticky Header elevation on scroll
  const header = document.querySelector(".site-header");
  window.addEventListener("scroll", () => {
    if (window.scrollY > 30) {
      header.classList.add("scrolled");
    } else {
      header.classList.remove("scrolled");
    }
  }, { passive: true });
}

// ==========================================
// 8. QR MODE & URL HASH HANDLING
// ==========================================
function checkQrMode() {
  const params = new URLSearchParams(window.location.search);
  const isQr = params.get("mode") === "qr" || window.location.hash === "#qr";

  if (isQr) {
    document.body.classList.add("qr-direct-mode");
    const indicator = document.getElementById("qrModeIndicator");
    if (indicator) {
      indicator.style.display = "inline-flex";
    }
    // Scroll directly to restaurant menu smoothly
    const menuSec = document.getElementById("menu");
    if (menuSec) {
      setTimeout(() => {
        menuSec.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 300);
    }
  }
}

// ==========================================
// 9. INITIALIZATION
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
  // Bind Language buttons
  document.querySelectorAll(".lang-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      setLanguage(btn.dataset.lang);
    });
  });

  // Search input binding
  const searchInput = document.getElementById("menuSearchInput");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      currentMenuSearch = e.target.value.trim();
      renderRestaurantMenu();
    });
  }

  // Lightbox controls
  const lightboxModal = document.getElementById("lightboxModal");
  if (lightboxModal) {
    document.getElementById("lightboxClose").addEventListener("click", closeLightbox);
    document.getElementById("lightboxNext").addEventListener("click", nextLightboxImage);
    document.getElementById("lightboxPrev").addEventListener("click", prevLightboxImage);
    lightboxModal.addEventListener("click", (e) => {
      if (e.target === lightboxModal) closeLightbox();
    });
  }

  // Keyboard navigation for lightbox
  document.addEventListener("keydown", (e) => {
    if (!lightboxModal.classList.contains("open")) return;
    if (e.key === "Escape") closeLightbox();
    if (e.key === "ArrowRight") nextLightboxImage();
    if (e.key === "ArrowLeft") prevLightboxImage();
  });

  // Booking success modal close
  const bookSuccessClose = document.getElementById("bookingSuccessClose");
  if (bookSuccessClose) {
    bookSuccessClose.addEventListener("click", closeBookingSuccessModal);
  }

  // Initialize components
  setupNavigation();
  setupGallery();
  setupBookingForm();
  setLanguage(currentLang);
  checkQrMode();
});
