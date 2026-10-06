export interface Product {
  id: number;
  name: string;
  price_ron: number;
  rating: number;
  review_count: number;
  cash_on_delivery: boolean;
  store: string;
  url: string;
  image_url: string | null;
}

export interface SearchResponse {
  query: string;
  products: Product[];
  total: number;
}

export interface Preferences {
  user_id: number;
  cash_only: boolean;
  open_package: boolean;
  min_rating: number;
  max_price: number | null;
}

export interface PreferencesUpdateRequest {
  cash_only: boolean;
  open_package: boolean;
  min_rating: number;
  max_price: number | null;
}
