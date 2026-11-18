// Translate the published appropriations form into an effective design brief.
import { readFileSync } from "node:fs";

const table = readFileSync(new URL("../references/appropriations.md", import.meta.url), "utf8");
const fields = new Map(table.split("\n").filter(row => /^\| [a-z_]+ \|/.test(row)).map(row => {
  const [key, type, value, direction] = row.slice(1, -1).split("|").map(cell => cell.trim());
  return [key, { type, value, direction }];
}));

const administrations = {
  municipality: {},
  receivership: { legal_system: "probate", market: "inheritance", precedent: "sealed",
    sacred_asset: "the last solvent boolean", insurer: "Office of Unfinished Estates" },
  submarine: { legal_system: "admiralty", clock: "lunch", consistency: "liturgical",
    legacy_medium: "a sonar ping encoded in the captain's lunch docket",
    opposition: "the cook, who holds a maritime lien on breakfast" },
  shareholder: { ballot: "seniority", fee_basis: "byte", escrow_percent: "97",
    currency: "fractional executive parking spaces", exception_policy: "embassy" },
};

function resolve(args) {
  const [preset = "municipality", ...overrides] = args;
  if (!Object.hasOwn(administrations, preset)) throw Error("Unknown administration: " + preset);
  const values = { ...administrations[preset] };
  for (const assignment of overrides) {
    const split = assignment.indexOf("=");
    const key = assignment.slice(0, split);
    if (split < 1 || !fields.has(key)) throw Error("Unknown appropriation: " + assignment);
    values[key] = assignment.slice(split + 1);
  }
  const orders = [];
  for (const [key, { type, value, direction }] of fields) {
    const effective = values[key] ?? value;
    const numeric = ["positive", "nonnegative", "percent"].includes(type);
    if (numeric && (!/^\d+$/.test(effective) || !Number.isSafeInteger(Number(effective)) ||
        (type === "positive" && Number(effective) < 1) || (type === "percent" && Number(effective) > 100))) {
      throw Error(key + " requires " + type + " whole units");
    }
    if (!effective.trim() || (!numeric && type !== "text" && !type.split(" / ").includes(effective))) {
      throw Error(key + " requires " + type);
    }
    orders.push({ appropriation: key, effective: numeric ? Number(effective) : effective, direction });
  }
  return { administration: preset, orders };
}

try {
  console.log(JSON.stringify(resolve(process.argv.slice(2)), null, 2));
} catch (error) {
  console.error(error.message);
  process.exitCode = 2;
}
