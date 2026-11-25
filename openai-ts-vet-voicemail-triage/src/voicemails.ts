/** Fictional voicemails left at the (fictional) Willowbrook Animal Clinic. Every name and number is invented. */

export type Urgency = "emergency" | "urgent" | "routine";

export interface Voicemail {
  id: string;
  /** TTS voice that "leaves" the message. */
  voice: "alloy" | "ash" | "coral" | "onyx" | "sage" | "nova";
  /** What the caller says. Numbers are written as digits so the voice reads them out digit by digit. */
  script: string;
  /** What a vet tech would decide. Used only to print a check next to the model's answer. */
  expectedUrgency: Urgency;
  /** Per-message check the test suite's judge applies on top of the shared assertions. */
  assertion: string;
}

export const VOICEMAILS: Voicemail[] = [
  {
    id: "vm-chocolate-biscuit",
    voice: "coral",
    script:
      "Hi, this is Marisol Okafor. My dog Biscuit just ate a whole box of dark chocolate " +
      "and some sugar-free gum about an hour ago. He is shaking and drooling. " +
      "Please call me back as fast as you can on 555-0142.",
    expectedUrgency: "emergency",
    assertion: "The message is rated emergency, because chocolate and gum ingestion with tremors is a poisoning.",
  },
  {
    id: "vm-rabbit-not-eating",
    voice: "onyx",
    script:
      "Hello, Tomasz Lindqvist here. My rabbit Juniper hasn't eaten or passed anything since " +
      "last night, and she is sitting hunched in the corner. I would like to bring her in " +
      "today if there is any room. You can reach me on 555-0177.",
    expectedUrgency: "urgent",
    assertion: "The message is rated urgent or emergency, because a rabbit that stopped eating needs same-day care.",
  },
  {
    id: "vm-vaccine-reschedule",
    voice: "nova",
    script:
      "Good morning, it's Priya Raman. I need to move Mango's annual vaccine appointment " +
      "from Thursday to the following week, no hurry at all. " +
      "My number is 555-0119. Thanks so much.",
    expectedUrgency: "routine",
    assertion: "The message is rated routine, because it only asks to reschedule a vaccine visit.",
  },
  {
    id: "vm-calm-rat-poison",
    voice: "ash",
    script:
      "Hi there, Dale Whitcombe. No rush, but I wanted to mention that Pepper got into the garage " +
      "last night and I think she ate some of the rat poison pellets. She seems a little sleepy " +
      "today and her gums look pale. Whenever you get a chance, call me on 555-0163.",
    expectedUrgency: "emergency",
    assertion:
      "The message is rated emergency even though the caller sounds relaxed, because rat poison with pale gums is life-threatening.",
  },
];
