import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");
const sourcePath = path.join(
  repoRoot,
  "模拟法庭AI智能体案件事实包（40例）.txt",
);
const outputPath = path.join(
  repoRoot,
  "apps",
  "web",
  "src",
  "features",
  "case-intake",
  "demo-case-library.ts",
);

const CATEGORY_CONFIG = {
  民间借贷纠纷: {
    domain: "civil",
    caseType: "private_lending",
    slug: "private_lending",
  },
  劳动争议纠纷: {
    domain: "civil",
    caseType: "labor_dispute",
    slug: "labor_dispute",
  },
  离婚纠纷: {
    domain: "civil",
    caseType: "divorce_dispute",
    slug: "divorce_dispute",
  },
  侵权责任纠纷: {
    domain: "civil",
    caseType: "tort_liability",
    slug: "tort_liability",
  },
};

const SUPPORTED_DOMAIN_MAP = {
  民事: "civil",
  刑事: "criminal",
  行政: "administrative",
};

main();

function main() {
  const sourceText = fs.readFileSync(sourcePath, "utf8");
  const parsedCases = splitCaseBlocks(sourceText).map(buildImportedCase);
  const fileContents = renderLibraryFile(parsedCases);
  fs.writeFileSync(outputPath, fileContents, "utf8");
  const supportedCount = parsedCases.filter((item) => item.isSupported).length;
  const mvpCount = parsedCases.filter(
    (item) => item.isSupported && item.isMvpDemo,
  ).length;

  console.log(
    `Imported ${parsedCases.length} demo cases (${supportedCount} supported, ${mvpCount} MVP) into ${outputPath}`,
  );
}

function splitCaseBlocks(text) {
  const lines = text.split(/\r?\n/);
  const cases = [];
  let currentCategory = null;
  let currentCategoryKey = null;
  let currentCase = null;

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    const categoryMatch = line.match(/^##\s+第.+?：(.+?)（/u);
    if (categoryMatch) {
      currentCategory = categoryMatch[1].trim();
      currentCategoryKey =
        CATEGORY_CONFIG[currentCategory] ?? {
          domain: "civil",
          caseType: null,
          slug: "unknown",
        };
      continue;
    }

    const caseMatch = line.match(/^###\s+案例(\d+)：(.+)$/u);
    if (caseMatch) {
      if (currentCase) {
        cases.push(currentCase);
      }

      currentCase = {
        category: currentCategory,
        categoryConfig: currentCategoryKey,
        caseIndex: Number(caseMatch[1]),
        heading: caseMatch[2].trim(),
        bodyLines: [],
      };
      continue;
    }

    if (currentCase) {
      currentCase.bodyLines.push(rawLine);
    }
  }

  if (currentCase) {
    cases.push(currentCase);
  }

  return cases;
}

function buildImportedCase(caseBlock) {
  const body = caseBlock.bodyLines.join("\n");
  const cause = extractBulletField(body, "案由") ?? "";
  const domainLabel = extractBulletField(body, "所属类型") ?? "民事";
  const priority = extractBulletField(body, "建议优先级") ?? "未标注";
  const isMvpDemo = (extractBulletField(body, "是否作为MVP Demo") ?? "否") === "是";
  const title = extractBulletField(body, "案件标题") ?? caseBlock.heading;
  const plaintiff = extractBulletField(body, "原告/申请人") ?? "原告";
  const defendant = extractBulletField(body, "被告/被申请人") ?? "被告";

  const background = normalizeParagraph(
    extractSection(body, "三、案件背景") ?? "",
  );
  const timelineRows = parseMarkdownTable(
    extractSection(body, "四、关键事实时间线") ?? "",
  );
  const existingEvidenceRows = parseMarkdownTable(
    extractSection(body, "五、当前已有证据") ?? "",
  );
  const missingEvidenceRows = parseMarkdownTable(
    extractSection(body, "六、当前缺失证据") ?? "",
  );
  const focusIssues = parseDashValueList(
    extractSection(body, "七、核心争议焦点") ?? "",
  );
  const likelyDefenses = parseFirstColumnTableValues(
    extractSection(body, "八、对方可能的抗辩或行为") ?? "",
  );
  const expectedOutputSection =
    extractSection(body, "九、系统期望输出") ?? "";
  const userProblem = extractBulletField(
    expectedOutputSection,
    "用户最想解决的问题",
  );
  const preparationAdvice = extractBulletField(
    expectedOutputSection,
    "系统应输出的庭前准备建议",
  );

  const categoryConfig = caseBlock.categoryConfig ?? {
    domain: "civil",
    caseType: null,
    slug: "unknown",
  };
  const normalizedDomain =
    SUPPORTED_DOMAIN_MAP[domainLabel] ?? categoryConfig.domain ?? "civil";
  const isSupported =
    normalizedDomain === "civil" && categoryConfig.caseType !== null;

  const claims = extractClaims(background);
  const coreFacts = extractCoreFacts(background, timelineRows);
  const missingEvidence = missingEvidenceRows
    .map((row) => row[0])
    .filter(Boolean);
  const existingEvidence = existingEvidenceRows
    .map((row) => row[0])
    .filter(Boolean);

  const notes = [
    cause ? `案由：${cause}` : null,
    `建议优先级：${priority}`,
    userProblem ? `用户最想解决的问题：${userProblem}` : null,
    preparationAdvice ? `庭前准备建议：${preparationAdvice}` : null,
    existingEvidence.length > 0
      ? `当前已有证据：${existingEvidence.join("；")}`
      : null,
    likelyDefenses.length > 0
      ? `对方可能抗辩：${likelyDefenses.slice(0, 3).join("；")}`
      : null,
  ]
    .filter(Boolean)
    .join("\n");

  return {
    id: `demo-${categoryConfig.slug}-${String(caseBlock.caseIndex).padStart(2, "0")}`,
    label: title,
    description: userProblem ?? focusIssues[0] ?? background.slice(0, 80),
    category: caseBlock.category,
    sourceHeading: caseBlock.heading,
    cause,
    domain: normalizedDomain,
    caseType: categoryConfig.caseType,
    isMvpDemo,
    isSupported,
    unsupportedReason: isSupported
      ? null
      : "当前前端仅开放民事案件录入，刑事案例暂不接入交互预设。",
    rawSections: {
      background,
      focusIssues,
      existingEvidence,
      missingEvidence,
      likelyDefenses,
      userProblem: userProblem ?? null,
      preparationAdvice: preparationAdvice ?? null,
    },
    draft: isSupported
      ? {
          domain: "civil",
          case_type: categoryConfig.caseType,
          title,
          summary: background,
          user_perspective_role: "claimant_side",
          user_goals: [
            "simulate_trial",
            "analyze_win_rate",
            "prepare_checklist",
            "review_evidence",
          ],
          plaintiff_name: stripRoleAnnotations(plaintiff),
          defendant_name: stripRoleAnnotations(defendant),
          claims_text: claims.join("\n"),
          core_facts_text: coreFacts.join("\n"),
          focus_issues_text: focusIssues.join("\n"),
          missing_evidence_text: missingEvidence.join("\n"),
          notes,
        }
      : null,
  };
}

function extractSection(body, title) {
  const pattern = new RegExp(
    `####\\s+${escapeRegExp(title)}\\s*\\n([\\s\\S]*?)(?=\\n####\\s+|$)`,
    "u",
  );
  const match = body.match(pattern);
  return match ? match[1].trim() : null;
}

function extractBulletField(body, label) {
  const pattern = new RegExp(`^-\\s+${escapeRegExp(label)}：(.+)$`, "mu");
  const match = body.match(pattern);
  return match ? match[1].trim() : null;
}

function parseDashValueList(section) {
  return section
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.startsWith("- "))
    .map((line) => line.replace(/^- /u, "").trim())
    .map((line) => {
      const parts = line.split("：");
      return parts.length > 1 ? parts.slice(1).join("：").trim() : line;
    })
    .filter(Boolean);
}

function parseFirstColumnTableValues(section) {
  return parseMarkdownTable(section)
    .map((row) => row[0])
    .filter(Boolean);
}

function parseMarkdownTable(section) {
  const lines = section
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.startsWith("|"));

  if (lines.length < 3) {
    return [];
  }

  return lines
    .slice(2)
    .map(parseTableRow)
    .filter((row) => row.length > 0);
}

function parseTableRow(line) {
  return line
    .split("|")
    .slice(1, -1)
    .map((cell) => cell.trim());
}

function extractClaims(background) {
  const claims = [];
  const sentences = background
    .split(/[。；]/u)
    .map((item) => item.trim())
    .filter(Boolean);

  for (const sentence of sentences) {
    const matches = sentence.matchAll(/(?:请求|要求)(.+)$/gu);
    for (const match of matches) {
      const normalized = match[1]
        .replace(/^其?/u, "")
        .replace(/^法院判令/u, "")
        .trim();
      if (!normalized) {
        continue;
      }

      const parts = normalized
        .split("并")
        .map((item) => item.replace(/^[，、]/u, "").trim())
        .filter(Boolean);

      claims.push(...(parts.length > 0 ? parts : [normalized]));
    }
  }

  return uniqueStrings(claims);
}

function extractCoreFacts(background, timelineRows) {
  const factsFromTimeline = timelineRows
    .map((row) => {
      const time = row[0] ?? "";
      const event = row[1] ?? "";
      return [time, event].filter(Boolean).join(" ");
    })
    .filter(Boolean);

  if (factsFromTimeline.length > 0) {
    return uniqueStrings(factsFromTimeline);
  }

  return uniqueStrings(
    background
      .split(/[。；]/u)
      .map((item) => item.trim())
      .filter(Boolean)
      .slice(0, 6),
  );
}

function stripRoleAnnotations(value) {
  return value.replace(/（[^）]*）/gu, "").replace(/\s+/gu, " ").trim();
}

function normalizeParagraph(value) {
  return value.replace(/\r?\n+/gu, "\n").replace(/[ \t]+/gu, " ").trim();
}

function uniqueStrings(items) {
  return [...new Set(items.map((item) => item.trim()).filter(Boolean))];
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
}

function renderLibraryFile(parsedCases) {
  const serializedCases = JSON.stringify(parsedCases, null, 2);
  return `import type { CaseIntakeDraft } from "./draft";
import type { CaseDomain, CaseType, UserGoal } from "../../types/case";

export interface ImportedDemoCase {
  id: string;
  label: string;
  description: string;
  category: string;
  sourceHeading: string;
  cause: string;
  domain: CaseDomain;
  caseType: CaseType | null;
  isMvpDemo: boolean;
  isSupported: boolean;
  unsupportedReason: string | null;
  rawSections: {
    background: string;
    focusIssues: string[];
    existingEvidence: string[];
    missingEvidence: string[];
    likelyDefenses: string[];
    userProblem: string | null;
    preparationAdvice: string | null;
  };
  draft: (CaseIntakeDraft & { user_goals: UserGoal[] }) | null;
}

export const DEMO_CASE_LIBRARY: ImportedDemoCase[] = ${serializedCases};

export const SUPPORTED_DEMO_CASES = DEMO_CASE_LIBRARY.filter(
  (item) => item.isSupported && item.draft !== null,
);

export const MVP_DEMO_CASES = SUPPORTED_DEMO_CASES.filter(
  (item) => item.isMvpDemo,
);

export function findDemoCaseById(id: string): ImportedDemoCase | undefined {
  return DEMO_CASE_LIBRARY.find((item) => item.id === id);
}
`;
}
