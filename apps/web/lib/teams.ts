export const TEAMS = {
  RCB: { name: "Royal Challengers Bengaluru", short: "RCB", color: "#EC1C24", city: "Bengaluru", home: "M. Chinnaswamy Stadium" },
  CSK: { name: "Chennai Super Kings", short: "CSK", color: "#FFCB05", city: "Chennai", home: "MA Chidambaram Stadium" },
  MI:  { name: "Mumbai Indians", short: "MI", color: "#004BA0", city: "Mumbai", home: "Wankhede Stadium" },
  KKR: { name: "Kolkata Knight Riders", short: "KKR", color: "#3A225D", city: "Kolkata", home: "Eden Gardens" },
  SRH: { name: "Sunrisers Hyderabad", short: "SRH", color: "#FF822A", city: "Hyderabad", home: "Rajiv Gandhi Intl. Cricket Stadium" },
  RR:  { name: "Rajasthan Royals", short: "RR", color: "#EA1A85", city: "Jaipur", home: "Sawai Mansingh Stadium" },
  DC:  { name: "Delhi Capitals", short: "DC", color: "#004C93", city: "Delhi", home: "Arun Jaitley Stadium" },
  PBKS:{ name: "Punjab Kings", short: "PBKS", color: "#DD1F2D", city: "Mohali", home: "Maharaja Yadavindra Singh Intl. Cricket Stadium" },
  GT:  { name: "Gujarat Titans", short: "GT", color: "#1C1C1C", city: "Ahmedabad", home: "Narendra Modi Stadium" },
  LSG: { name: "Lucknow Super Giants", short: "LSG", color: "#ACE5F3", city: "Lucknow", home: "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium" },
} as const;

export type TeamKey = keyof typeof TEAMS;

export const TEAM_KEYS = Object.keys(TEAMS) as TeamKey[];

export function getTeamBySlug(slug: string): TeamKey | null {
  const upper = slug.toUpperCase();
  if (upper in TEAMS) return upper as TeamKey;
  return null;
}

export function getTeamData(slug: string) {
  const key = getTeamBySlug(slug);
  if (!key) return null;
  return TEAMS[key];
}
