import DataTable from "./table";

export default DataTable;

export { default as TablePagination } from "./table-pagination";
export { default as TableSearch } from "./table-search";
export {
  default as TableFilter,
  SelectFilter,
  MultiSelectFilter,
  BooleanFilter,
  DateFilter,
} from "./table-filter";

export type {
  TableQueryParams,
  DataTableProps,
  TableMeta,
  Fetcher,
  FetcherResult,
} from "./table";
export type { TableSearchProps } from "./table-search";
export type {
  FilterConfig,
  FilterState,
  FilterValue,
  FilterType,
  FilterOption,
  BooleanFilterValue,
  BooleanFilterProps,
  SelectFilterValue,
  SelectFilterProps,
  SelectMultiFilterValue,
  SelectMultiFilterProps,
  DateFilterValue,
  DateFilterProps,
} from "./types";

export { calculatePagination, cn } from "./utils";
