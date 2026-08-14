import { webLightTheme, type Theme } from "@fluentui/react-components";

// 국내 은행 홈페이지에서 흔히 쓰이는 골드(금색) 포인트 컬러 + 네이비 텍스트 조합을
// 참고한 커스텀 테마입니다. 특정 브랜드의 로고·문구·이미지는 사용하지 않습니다.
const GOLD = "#FFB600";
const GOLD_HOVER = "#E6A200";
const GOLD_PRESSED = "#CC8F00";
const GOLD_SOFT = "#FFE9B3";
const NAVY = "#1B2A4A";
const NAVY_SOFT = "#2E3F63";

export const bankStyleTheme: Theme = {
  ...webLightTheme,

  // 버튼/포커스 등 브랜드 배경색
  colorBrandBackground: GOLD,
  colorBrandBackgroundHover: GOLD_HOVER,
  colorBrandBackgroundPressed: GOLD_PRESSED,
  colorBrandBackgroundSelected: GOLD_HOVER,
  colorBrandBackgroundInverted: GOLD,
  colorBrandBackgroundInvertedHover: GOLD_HOVER,
  colorBrandBackgroundInvertedPressed: GOLD_PRESSED,

  // 골드 배경 위에 올라가는 텍스트는 네이비로 (밝은 배경 대비 확보)
  colorNeutralForegroundOnBrand: NAVY,

  // 링크·강조 텍스트
  colorBrandForeground1: NAVY,
  colorBrandForeground2: NAVY_SOFT,
  colorBrandForegroundLink: NAVY,
  colorBrandForegroundLinkHover: NAVY_SOFT,
  colorBrandForegroundLinkPressed: NAVY,

  // Compound 컴포넌트(Checkbox 등) 브랜드 색
  colorCompoundBrandBackground: GOLD,
  colorCompoundBrandBackgroundHover: GOLD_HOVER,
  colorCompoundBrandBackgroundPressed: GOLD_PRESSED,
  colorCompoundBrandStroke: GOLD,
  colorCompoundBrandStrokeHover: GOLD_HOVER,
  colorCompoundBrandStrokePressed: GOLD_PRESSED,

  // 테두리/포커스 링
  colorBrandStroke1: GOLD,
  colorBrandStroke2: GOLD_SOFT,

  // 카드/버튼 모서리를 더 둥글게 (은행 앱 특유의 부드러운 카드 느낌)
  borderRadiusMedium: "10px",
  borderRadiusLarge: "14px",
  borderRadiusXLarge: "20px",
};

export const bankStylePalette = {
  gold: GOLD,
  goldHover: GOLD_HOVER,
  goldSoft: GOLD_SOFT,
  navy: NAVY,
  navySoft: NAVY_SOFT,
};
