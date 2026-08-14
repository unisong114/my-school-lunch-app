// 내부 API(src/openapi.json) 계약에 대응하는 타입 정의.

export interface School {
  eduOfficeCode: string;
  eduOfficeName: string;
  schoolCode: string;
  schoolName: string;
  schoolKind?: string | null;
  region?: string | null;
  address?: string | null;
}

export interface SchoolSearchResponse {
  schools: School[];
}

export interface MealDish {
  name: string;
  allergies: number[];
}

export interface DailyMeal {
  date: string;
  mealName: string;
  dishes: MealDish[];
  calorie?: string | null;
  nutrition?: string | null;
  origin?: string | null;
}

export interface MealQueryResponse {
  schoolCode: string;
  fromDate: string;
  toDate: string;
  meals: DailyMeal[];
}
