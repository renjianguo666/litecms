/*
 * boolean filter
 */
export type BooleanFilterValue = boolean | undefined;

export interface BooleanFilterProps {
  value?: BooleanFilterValue;
  onChange: (value: BooleanFilterValue) => void;
  trueText?: string;
  falseText?: string;
  placeholder?: string;
  label?: string;
}

/*
 * select filter
 */
export interface FilterOption {
  label: string;
  value: string;
}

export type SelectFilterValue = string | number | undefined;
export type SelectMultiFilterValue = SelectFilterValue[];

export interface SelectFilterProps {
  options: FilterOption[];
  value: SelectFilterValue;
  onChange: (value: SelectFilterValue) => void;
  label?: string;
  placeholder?: string;
}

export interface SelectMultiFilterProps {
  options: FilterOption[];
  value: SelectMultiFilterValue;
  onChange: (value: SelectMultiFilterValue) => void;
  label?: string;
  placeholder?: string;
}

/*
 * date filter
 */
export type DateFilterValue = string | undefined; // ISO date string

export interface DateFilterProps {
  value?: DateFilterValue;
  onChange: (value: DateFilterValue) => void;
  label?: string;
  placeholder?: string;
}

/*
 * filter config
 */
export type FilterType = 'select' | 'multi-select' | 'boolean' | 'date';

export type FilterValue = 
  | BooleanFilterValue 
  | SelectFilterValue 
  | SelectMultiFilterValue 
  | DateFilterValue
  | null 
  | undefined;

export interface FilterConfig {
  name: string;
  variant: FilterType;
  label: string;
  placeholder?: string;
  options?: FilterOption[];
  trueText?: string;
  falseText?: string;
}

export type FilterState = Record<string, FilterValue>;
