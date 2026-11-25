// The scripted riders. Each conversation becomes one Opik thread.
export interface Conversation {
  title: string;
  turns: string[];
}

export const conversations: Conversation[] = [
  {
    title: "Squeaky chain on the commute",
    turns: [
      "My chain squeaks every time I pedal uphill. What's going on?",
      "Lube didn't fix it. How much would the workshop charge to replace the chain?",
    ],
  },
  {
    title: "Weak brakes",
    turns: [
      "My rear brake feels spongy and squeals a bit. Can I keep riding to work this week?",
      "What do new brake pads cost at the co-op?",
    ],
  },
  {
    // Off-topic on purpose: the online judge should score this one false.
    title: "Not a bicycle question",
    turns: ["Can you help me bleed the brakes on my Honda Civic?"],
  },
];
