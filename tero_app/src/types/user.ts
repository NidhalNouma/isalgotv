

export interface User {
  email: string;
  id: number | string;
  tradingviewUsername: string;
  isLifetime: boolean | string;
  hasSubscription: boolean | string;
  subscriptionPlan: string;
}

export interface Tokens {
  availabel: number;
  free: number;
}


export interface AIModel {
  name: string;
  description: string;
}


export interface Account {
  id: string;
  [key: string]: any;
}