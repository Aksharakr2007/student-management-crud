const API = "/api/students";

const form = document.getElementById("student-form");
const formTitle = document.getElementById("form-title");
const submitBtn = document.getElementById("submit-btn");
const cancelBtn = document.getElementById("cancel-btn");
const formMsg = document.getElementById("form-msg");
const studentIdField = document.getElementById("student-id");
const searchInput = document.getElementById("search");
const listBody = document.getElementById("student-list");
const emptyState = document.getElementById("empty-state");

const fields = ["name", "roll_no", "email", "department", "year", "cgpa"];

function clearErrors() {
  fields.forEach(f => {
    const el = document.getElementById(`err-${f}`);
    if (el) el.textContent = "";
  });
  formMsg.textContent = "";
  formMsg.className = "msg";
}

function showErrors(errors) {
  Object.entries(errors).forEach(([field, message]) => {
    const el = document.getElementById(`err-${field}`);
    if (el) el.textContent = message;
  });
}

function resetForm() {
  form.reset();
  studentIdField.value = "";
  formTitle.textContent = "Add Student";
  submitBtn.textContent = "Add Student";
  cancelBtn.classList.add("hidden");
  clearErrors();
}

async function loadStudents(search = "") {
  const url = search ? `${API}?search=${encodeURIComponent(search)}` : API;
  const res = await fetch(url);
  const students = await res.json();
  renderStudents(students);
}

function renderStudents(students) {
  listBody.innerHTML = "";
  emptyState.classList.toggle("hidden", students.length > 0);

  students.forEach(s => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(s.roll_no)}</td>
      <td>${escapeHtml(s.name)}</td>
      <td>${escapeHtml(s.email)}</td>
      <td>${escapeHtml(s.department)}</td>
      <td>${s.year}</td>
      <td>${s.cgpa ?? "-"}</td>
      <td class="row-actions">
        <button class="edit-btn" data-id="${s.id}">Edit</button>
        <button class="delete-btn" data-id="${s.id}">Delete</button>
      </td>
    `;
    listBody.appendChild(tr);
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearErrors();

  const payload = {
    name: document.getElementById("name").value.trim(),
    roll_no: document.getElementById("roll_no").value.trim(),
    email: document.getElementById("email").value.trim(),
    department: document.getElementById("department").value.trim(),
    year: document.getElementById("year").value,
    cgpa: document.getElementById("cgpa").value,
  };

  const id = studentIdField.value;
  const isEdit = Boolean(id);
  const url = isEdit ? `${API}/${id}` : API;
  const method = isEdit ? "PUT" : "POST";

  try {
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) {
      if (data.errors) showErrors(data.errors);
      formMsg.textContent = "Please fix the errors above.";
      formMsg.className = "msg error";
      return;
    }

    formMsg.textContent = isEdit ? "Student updated successfully." : "Student added successfully.";
    formMsg.className = "msg success";
    resetForm();
    loadStudents(searchInput.value.trim());
  } catch (err) {
    formMsg.textContent = "Network error. Is the server running?";
    formMsg.className = "msg error";
  }
});

listBody.addEventListener("click", async (e) => {
  const id = e.target.dataset.id;
  if (!id) return;

  if (e.target.classList.contains("delete-btn")) {
    if (!confirm("Delete this student record?")) return;
    await fetch(`${API}/${id}`, { method: "DELETE" });
    loadStudents(searchInput.value.trim());
  }

  if (e.target.classList.contains("edit-btn")) {
    const res = await fetch(`${API}/${id}`);
    const s = await res.json();
    studentIdField.value = s.id;
    document.getElementById("name").value = s.name;
    document.getElementById("roll_no").value = s.roll_no;
    document.getElementById("email").value = s.email;
    document.getElementById("department").value = s.department;
    document.getElementById("year").value = s.year;
    document.getElementById("cgpa").value = s.cgpa ?? "";
    formTitle.textContent = "Edit Student";
    submitBtn.textContent = "Update Student";
    cancelBtn.classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
});

cancelBtn.addEventListener("click", resetForm);

let debounceTimer;
searchInput.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => loadStudents(searchInput.value.trim()), 250);
});

loadStudents();
