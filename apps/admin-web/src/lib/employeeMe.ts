export type EmployeeMeUser = {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  phone_number: string | null;
};

export type EmployeeMeEmployee = {
  id: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  date_of_birth: string | null;
  date_of_joining: string;
  status: string;
  department_name: string | null;
  designation_name: string | null;
  branch_name: string | null;
};

export type EmployeeMeContact = {
  id: string;
  personal_email: string | null;
  mobile_number: string;
  alternate_number: string | null;
  present_address: string;
  permanent_address: string;
  emergency_contact_name: string;
  emergency_contact_number: string;
};

export type EmployeeMeProfile = {
  user: EmployeeMeUser;
  employee: EmployeeMeEmployee | null;
  contact: EmployeeMeContact | null;
  has_employee: boolean;
  has_bank: boolean;
  has_assets: boolean;
};

export type EmployeeMeBank = {
  id: string;
  bank_name: string;
  account_number_masked: string;
  ifsc_code: string;
  account_type: string;
};

export type EmployeeMeAsset = {
  id: string;
  assigned_date: string;
  asset_name: string;
  serial_number: string;
  category: string;
  asset_status: string;
};

export const EMPLOYEE_ME_QUERY_KEY = 'employee-me';
