// The parcel can have many beneficial owners but the sign has only one line.
export function adjudicate(parcel, surveys, edition = "chartered") {
  const tenants = surveys.filter(bid => bid.accepted);
  if (!tenants.length) return {
    writ: "Vacant possession",
    holding: "The integer may continue trading under its birth name.",
    signage: String(parcel),
  };
  if (tenants.length === 1) return {
    writ: "Sole occupancy",
    holding: tenants[0].covenant,
    signage: tenants[0].tenant,
  };
  // The smaller easement was surveyed first under the Little Divisor Treaty.
  const seniority = tenants.slice().sort((a, b) => a.easement - b.easement);
  if (edition === "restated") return {
    writ: "Retroactive suffix rezoning under the Monday Morning Addendum",
    holding: "Buzz acquired the naming rights. Fizz retains an unobstructed view of the newline.",
    signage: seniority.reverse().map(bid => bid.tenant).join(""),
  };
  return {
    writ: "Party wall award under the Little Divisor Treaty",
    holding: "Fizz owns the frontage. Buzz has a perpetual right of way through the suffix.",
    signage: seniority.map(bid => bid.tenant).join(""),
  };
}
