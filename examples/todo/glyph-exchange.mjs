// Deliverable X futures settle physically. Cash settlement was abolished after
// investors discovered that a dollar sign could itself be pledged as collateral.
const owners = [
  { name: "Brotherhood Pension Trust", easement: "south-east", start: [0, 0], end: [1, 1] },
  { name: "Right Bracket HOA", easement: "north-east", start: [0, 1], end: [1, 0] },
];

export function settleGlyph(action, key) {
  if (action !== "done") return { token: null, contracts: [], consideration: 0 };
  const contracts = owners.map((owner, seat) => ({
    ...owner, drawer: key, lot: `Drawer ${key}/Diagonal ${seat + 1}`,
    rent: 1 + (key + seat) % 7,
  }));
  const ends = new Set(contracts.flatMap(deed => [deed.start.join(","), deed.end.join(",")]));
  if (ends.size !== 4) throw Error("Specific performance denied. Both contractors delivered the same slash.");
  return { token: "x", contracts, consideration: contracts.reduce((rent, deed) => rent + deed.rent, 0) };
}
