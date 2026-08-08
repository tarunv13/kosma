/**
 * Classical upaya, keyed to the graha.
 *
 * A deliberate design decision: remedies are attached to **planets**, never
 * invented per yoga. There is a well-attested classical register of mantra,
 * daana and vara for each graha; there is no canonical "remedy for Gaja Kesari
 * Yoga", and generating one per combination would be precisely the invention
 * this project exists to prevent. So a yoga card offers the upaya of the
 * grahas that form it, and says that is what it is doing.
 *
 * Gemstones are included because they are part of the classical register and
 * their omission would be its own distortion — but they carry the loudest
 * caveat, because ratna prescription is genuinely contested, expensive, and
 * held by most practitioners to require a full chart reading rather than a
 * lookup table.
 */

export interface Remedy {
  graha: string;
  mantra: string;
  transliteration: string;
  gem: string;
  daana: string;
  vara: string;
}

export const REMEDIES: Record<string, Remedy> = {
  Sun: {
    graha: "Surya",
    mantra: "ॐ घृणिः सूर्याय नमः",
    transliteration: "Om Ghrini Suryaya Namah",
    gem: "Ruby (manikya)",
    daana: "wheat, jaggery, copper",
    vara: "Sunday",
  },
  Moon: {
    graha: "Chandra",
    mantra: "ॐ सों सोमाय नमः",
    transliteration: "Om Som Somaya Namah",
    gem: "Pearl (mukta)",
    daana: "rice, milk, silver",
    vara: "Monday",
  },
  Mars: {
    graha: "Mangala",
    mantra: "ॐ अं अङ्गारकाय नमः",
    transliteration: "Om Am Angarakaya Namah",
    gem: "Red coral (moonga)",
    daana: "red lentils, copper",
    vara: "Tuesday",
  },
  Mercury: {
    graha: "Budha",
    mantra: "ॐ बुं बुधाय नमः",
    transliteration: "Om Bum Budhaya Namah",
    gem: "Emerald (panna)",
    daana: "green gram, books",
    vara: "Wednesday",
  },
  Jupiter: {
    graha: "Brihaspati",
    mantra: "ॐ बृं बृहस्पतये नमः",
    transliteration: "Om Brim Brihaspataye Namah",
    gem: "Yellow sapphire (pukhraj)",
    daana: "turmeric, chana dal, saffron",
    vara: "Thursday",
  },
  Venus: {
    graha: "Shukra",
    mantra: "ॐ शुं शुक्राय नमः",
    transliteration: "Om Shum Shukraya Namah",
    gem: "Diamond (heera)",
    daana: "white cloth, curd, rice",
    vara: "Friday",
  },
  Saturn: {
    graha: "Shani",
    mantra: "ॐ शं शनैश्चराय नमः",
    transliteration: "Om Sham Shanaishcharaya Namah",
    gem: "Blue sapphire (neelam)",
    daana: "sesame, black cloth, iron",
    vara: "Saturday",
  },
  Rahu: {
    graha: "Rahu",
    mantra: "ॐ रां राहवे नमः",
    transliteration: "Om Ram Rahave Namah",
    gem: "Hessonite (gomed)",
    daana: "sesame, blankets",
    vara: "Saturday",
  },
  Ketu: {
    graha: "Ketu",
    mantra: "ॐ कें केतवे नमः",
    transliteration: "Om Kem Ketave Namah",
    gem: "Cat's eye (lehsunia)",
    daana: "sesame, blankets",
    vara: "Tuesday",
  },
};

export const REMEDY_CAVEAT =
  "Classical associations for the grahas that form this yoga, not a prescription " +
  "for it. No canonical remedy exists per yoga, so none is invented here.";

export const RATNA_CAVEAT =
  "Gemstones especially: most practitioners hold that ratna requires a full " +
  "reading of the whole chart, not a lookup by planet. Treat this as reference.";
