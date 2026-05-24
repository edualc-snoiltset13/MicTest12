import Papa, { ParseResult } from 'papaparse';
import { IEmployeeData } from '../types/employee';
import { ParserDateError } from './errors';

interface RawEmployeeRow {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  department: string;
  position: string;
  startDate: string;
  dateOfBirth: string;
  salary: string;
  phoneNumber?: string;
}

function parseDate(value: string): Date | null {
  if (!value || value.trim() === '') return null;
  const parsed = new Date(value.trim());
  return isNaN(parsed.getTime()) ? null : parsed;
}

export function parseCSVToEmployees(csvContent: string): IEmployeeData[] {
  const result: ParseResult<RawEmployeeRow> = Papa.parse<RawEmployeeRow>(csvContent, {
    header: true,
    skipEmptyLines: true,
    transformHeader: (header) => header.trim(),
    transform: (value) => value.trim(),
  });

  if (result.errors.length > 0) {
    const messages = result.errors.map((e) => `Row ${e.row}: ${e.message}`).join('; ');
    throw new Error(`CSV parse errors: ${messages}`);
  }

  const startDateErrors: number[] = [];
  const dateOfBirthErrors: number[] = [];

  const employees: IEmployeeData[] = result.data.map((row, index) => {
    const rowNumber = index + 2; // 1-based, accounting for header row

    const startDate = parseDate(row.startDate);
    if (startDate === null) startDateErrors.push(rowNumber);

    const dateOfBirth = parseDate(row.dateOfBirth);
    if (dateOfBirth === null) dateOfBirthErrors.push(rowNumber);

    return {
      id: row.id,
      firstName: row.firstName,
      lastName: row.lastName,
      email: row.email,
      department: row.department,
      position: row.position,
      startDate: startDate as Date,
      dateOfBirth: dateOfBirth as Date,
      salary: parseFloat(row.salary),
      ...(row.phoneNumber ? { phoneNumber: row.phoneNumber } : {}),
    };
  });

  if (startDateErrors.length > 0) {
    throw new ParserDateError('startDate', startDateErrors);
  }

  if (dateOfBirthErrors.length > 0) {
    throw new ParserDateError('dateOfBirth', dateOfBirthErrors);
  }

  return employees;
}
