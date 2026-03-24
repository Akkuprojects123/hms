// api.js

const API_BASE = '/api';

async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    if (body) {
        options.body = JSON.stringify(body);
    }
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || 'API Error');
    }
    return data;
}

const api = {
    lookupPatient: (phone) => apiCall(`/patient/${phone}`),
    registerPatient: (data) => apiCall('/patient', 'POST', data),
    loginPatient: (phone, password) => apiCall('/login/patient', 'POST', { phone, password }),
    loginDoctor: (username, password) => apiCall('/login/doctor', 'POST', { username, password }),
    createAppointment: (data) => apiCall('/appointment', 'POST', data),
    getDoctors: () => apiCall('/doctors'),
    getQueue: (doctorId = '') => apiCall(`/queue${doctorId ? '?doctor_id='+doctorId : ''}`),
    getAppointment: (id) => apiCall(`/appointment/${id}`),
    updateAppointmentStatus: (id, status) => apiCall(`/appointment/${id}/status`, 'PUT', { status }),
    createPrescription: (data) => apiCall('/prescription', 'POST', data),
    getPatientPrescriptions: (patientId) => apiCall(`/patient/${patientId}/prescriptions`),
    getPrescription: (id) => apiCall(`/prescription/${id}`),
    orderMedicine: (prescId) => apiCall('/medicine/order', 'POST', { prescription_id: prescId }),
    updateMedicineStatus: (prescId, status) => apiCall(`/medicine/order/${prescId}/status`, 'PUT', { status })
};

function showElement(id) {
    const el = document.getElementById(id);
    if(el) el.classList.remove('hidden');
}

function hideElement(id) {
    const el = document.getElementById(id);
    if(el) el.classList.add('hidden');
}
