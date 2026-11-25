/** One finished episode waiting for a title and a blurb. */
export interface Episode {
  show: string;
  guest: string;
  notes: string;
}

/**
 * Five episodes from the (fictional) Marrow & Moss Audio network. The notes are
 * deliberately dramatic, which is exactly what tempts a model into clickbait.
 */
export const EPISODES: Episode[] = [
  {
    show: "The Slow Boil",
    guest: "Ines Calloway",
    notes:
      "Ines cooked lunch in a school cafeteria for 41 years and kept a handwritten log of every soup she made. " +
      "Her notebooks hold 7,300 entries, including the day a blizzard left her feeding 200 stranded kids from one pot of lentils.",
  },
  {
    show: "Night Shift Radio",
    guest: "Tomasz Brandt",
    notes:
      "Tomasz is the overnight dispatcher for a river ferry that has never missed a crossing. " +
      "He talks about the 3 a.m. regulars, the one night the fog was so thick he guided a boat by singing, and why he refuses to retire.",
  },
  {
    show: "Tiny Maps",
    guest: "Dr. Priya Venkataraman",
    notes:
      "Priya is a cartographer who spent two years mapping a single apartment building: every stairwell, mailbox and rooftop pigeon coop. " +
      "The finished map hangs in the lobby and has changed how the neighbours treat each other.",
  },
  {
    show: "Second Hand Signal",
    guest: "Oskar Lindqvist",
    notes:
      "Oskar restores 1950s tube radios in a cramped Tallinn workshop. " +
      "He opens a set that was sealed in a cellar for sixty years and finds a folded letter tucked behind the dial.",
  },
  {
    show: "Small Hours Science",
    guest: "Marguerite Okafor",
    notes:
      "Marguerite is a retired postal worker who has counted moths in her garden every night since 2009. " +
      "Her data now feeds a national insect study, and she explains why the numbers have been dropping.",
  },
];
