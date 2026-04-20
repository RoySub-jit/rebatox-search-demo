import type { ReactNode } from "react";

type Column = {
  key: string;
  label: string;
  align?: "left" | "right";
};

type Row = {
  id: string;
  [key: string]: ReactNode;
};

type InfoTableProps = {
  columns: Column[];
  rows: Row[];
};

export function InfoTable({ columns, rows }: InfoTableProps) {
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={column.align === "right" ? "align-right" : ""}
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={column.align === "right" ? "align-right" : ""}
                >
                  {row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
