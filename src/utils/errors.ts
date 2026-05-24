export class ParserDateError extends Error {
  public readonly invalidRows: number[];
  public readonly field: string;

  constructor(field: string, invalidRows: number[]) {
    const rows = invalidRows.join(', ');
    super(`Invalid date value for field "${field}" at row(s): ${rows}`);
    this.name = 'ParserDateError';
    this.field = field;
    this.invalidRows = invalidRows;
    Object.setPrototypeOf(this, ParserDateError.prototype);
  }
}
