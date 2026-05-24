import axios from './axios';

export const wfhApi = {
  listMyRequests: () => axios.get('/wfh/requests/my/'),
  createRequest: (data: { start_date: string; end_date: string; reason: string; request_date?: string }) =>
    axios.post('/wfh/requests/', data),
  listAllRequests: () => axios.get('/wfh/requests/all/'),
  pendingApprovals: () => axios.get('/wfh/requests/pending-approvals/'),
  managerApprove: (id: string, remarks?: string) =>
    axios.post(`/wfh/requests/${id}/manager-approve/`, { remarks }),
  hrApprove: (id: string, remarks?: string) =>
    axios.post(`/wfh/requests/${id}/hr-approve/`, { remarks }),
  reject: (id: string, remarks?: string) => axios.post(`/wfh/requests/${id}/reject/`, { remarks }),
  cancel: (id: string, remarks?: string) => axios.post(`/wfh/requests/${id}/cancel/`, { remarks }),
  getPolicy: () => axios.get('/wfh/policy/'),
  updatePolicy: (data: Record<string, unknown>) => axios.put('/wfh/policy/', data),
  dashboard: () => axios.get('/wfh/dashboard/'),
  teamSummary: () => axios.get('/wfh/team-summary/'),
  sessionReport: () => axios.get('/wfh/session-report/'),
  productivityReport: () => axios.get('/wfh/productivity-report/'),
  employeeSummary: () => axios.get('/wfh/employee-summary/'),
  sessionScreenshots: (sessionId: string) => axios.get(`/wfh/sessions/${sessionId}/screenshots/`),
  screenshotImage: (screenshotId: string) =>
    axios.get(`/wfh/screenshots/${screenshotId}/`, { responseType: 'blob' }),
  trackerSettings: () => axios.get('/wfh/admin/tracker-settings/'),
  trackerDevices: () => axios.get('/wfh/admin/tracker-devices/'),
  auditLogs: () => axios.get('/wfh/admin/audit-logs/'),
};
