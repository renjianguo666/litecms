import { splitProps, type JSX } from "solid-js";
import { cn } from "@/lib/utils";

type TableProps = JSX.HTMLAttributes<HTMLTableElement>;

function Table(props: TableProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <div class="relative w-full overflow-auto">
      <table
        data-slot="table"
        class={cn("w-full caption-bottom text-sm", local.class)}
        {...others}
      />
    </div>
  );
}

type TableHeaderProps = JSX.HTMLAttributes<HTMLTableSectionElement>;

function TableHeader(props: TableHeaderProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <thead
      data-slot="table-header"
      class={cn("[&_tr]:border-b", local.class)}
      {...others}
    />
  );
}

type TableBodyProps = JSX.HTMLAttributes<HTMLTableSectionElement>;

function TableBody(props: TableBodyProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <tbody
      data-slot="table-body"
      class={cn("[&_tr:last-child]:border-0", local.class)}
      {...others}
    />
  );
}

type TableFooterProps = JSX.HTMLAttributes<HTMLTableSectionElement>;

function TableFooter(props: TableFooterProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <tfoot
      data-slot="table-footer"
      class={cn(
        "bg-muted/50 border-t font-medium [&>tr]:last:border-b-0",
        local.class,
      )}
      {...others}
    />
  );
}

type TableRowProps = JSX.HTMLAttributes<HTMLTableRowElement>;

function TableRow(props: TableRowProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <tr
      data-slot="table-row"
      class={cn(
        "border-b hover:bg-muted/50 data-[state=selected]:bg-muted",
        local.class,
      )}
      {...others}
    />
  );
}

type TableHeadProps = JSX.ThHTMLAttributes<HTMLTableCellElement>;

function TableHead(props: TableHeadProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <th
      data-slot="table-head"
      class={cn(
        "text-muted-foreground h-10 px-2 text-left align-middle font-medium [&:has([role=checkbox])]:pr-0 *:[[role=checkbox]]:translate-y-0.5",
        local.class,
      )}
      {...others}
    />
  );
}

type TableCellProps = JSX.TdHTMLAttributes<HTMLTableCellElement>;

function TableCell(props: TableCellProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <td
      data-slot="table-cell"
      class={cn(
        "p-2 align-middle [&:has([role=checkbox])]:pr-0 *:[[role=checkbox]]:translate-y-0.5",
        local.class,
      )}
      {...others}
    />
  );
}

type TableCaptionProps = JSX.HTMLAttributes<HTMLTableCaptionElement>;

function TableCaption(props: TableCaptionProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <caption
      data-slot="table-caption"
      class={cn("text-muted-foreground mt-4 text-sm", local.class)}
      {...others}
    />
  );
}

export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
};
export type {
  TableProps,
  TableHeaderProps,
  TableBodyProps,
  TableFooterProps,
  TableRowProps,
  TableHeadProps,
  TableCellProps,
  TableCaptionProps,
};
