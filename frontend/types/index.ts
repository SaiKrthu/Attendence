export type User = {
  id: number;
  email: string;
  role: "admin" | "employee";
  employee_id: string | null;
  full_name: string | null;
};

export type Employee = {
  id: number;
  employee_id: string;
  full_name: string;
  email: string;
  phone: string | null;
  department: string | null;
  designation: string | null;
  joining_date: string;
  status: "active" | "inactive";
  face_registered: boolean;
};

export type AttendanceRecord = {
  id: number;
  employee_id: string;
  employee_name: string;
  attendance_date: string;
  check_in_time: string | null;
  check_out_time: string | null;
  status: "present" | "late" | "absent" | "leave" | "half_day";
  working_hours: number | null;
};

export type DashboardSummary = {
  total_employees: number;
  present_today: number;
  absent_today: number;
  late_today: number;
  on_leave: number;
};

export type EmployeeSignupRequest = {
  id: number;
  employee_id: string;
  full_name: string;
  email: string;
  department: string;
  designation: string | null;
  created_at: string;
};
