document.addEventListener("DOMContentLoaded", () => {
  async function loadMeetings() {
    const response = await fetch("/api/meetings");
    const data = await response.json();
    const tbody = document.querySelector("#meetingsTable tbody");
    tbody.innerHTML = "";

    data.meetings.forEach(meeting => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${meeting.title}</td>
        <td>${meeting.date}</td>
        <td>${meeting.code}</td>
        <td><img src="${meeting.qr_url || `/static/qrcodes/${meeting.code}.png`}" alt="QR Code" /></td>
        <td><button onclick="deleteMeeting(${meeting.id})">Delete</button></td>
      `;
      tbody.appendChild(row);
    });
  }

  async function createMeeting(event) {
    event.preventDefault();
    const titleInput = document.getElementById("meetingTitle");
    const dateInput = document.getElementById("meetingDate");
  
    if (!titleInput || !dateInput) {
      alert("Missing form fields");
      return;
    }
  
    const title = titleInput.value;
    const date = dateInput.value;
  
    const response = await fetch("/api/meetings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, date })
    });
  
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Something went wrong." }));
      alert(error.detail);
      return;
    }
  
    const data = await response.json();
    alert(data.msg);
  
    titleInput.value = "";
    dateInput.value = "";
  
    loadMeetings();
  }
  

  async function deleteMeeting(id) {
    if (!confirm("Are you sure you want to delete this meeting?")) return;

    const response = await fetch(`/api/meetings/${id}`, { method: "DELETE" });
    const data = await response.json();
    alert(data.msg);
    loadMeetings();
  }

  async function loadMembers() {
    const response = await fetch("/api/members");
    const data = await response.json();
    const tbody = document.querySelector("#membersTable tbody");
    tbody.innerHTML = "";

    data.members.forEach(member => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${member.name}</td>
        <td>${member.email}</td>
        <td><button onclick="deleteMember(${member.id})">Delete</button></td>
      `;
      tbody.appendChild(row);
    });
  }

  async function deleteMember(id) {
    if (!confirm("Are you sure you want to delete this member?")) return;
  
    const response = await fetch(`/api/members/${id}`, { method: "DELETE" });
    const data = await response.json();
    alert(data.msg);
  
    loadMembers();      
    loadAttendance();    
  }
  

  async function loadAttendance() {
    try {
      const name = document.getElementById("filterName").value;
      const date = document.getElementById("filterDate").value;
  
      let query = "/api/attendance";
      if (name) query += `?user_name=${encodeURIComponent(name)}`;
      else if (date) query += `?meeting_date=${encodeURIComponent(date)}`;
  
      const response = await fetch(query);
  
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Failed to load attendance." }));
        alert(error.detail);
        return;
      }
  
      const data = await response.json();
      const tbody = document.querySelector("#attendanceTable tbody");
      tbody.innerHTML = "";
  
      data.attendance.forEach(record => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${record.user_name}</td>
          <td>${record.user_email}</td>
          <td>${record.meeting_title}</td>
          <td>${record.meeting_date}</td>
        `;
        tbody.appendChild(row);
      });
  
    } catch (err) {
      console.error("Error loading attendance:", err);
      alert("Something went wrong while loading attendance.");
    }
  }
  

  function downloadCSV(url) {
    window.location.href = url;
  }

  const form = document.querySelector("form[onsubmit='createMeeting(event)']");
  if (form) {
    form.onsubmit = createMeeting;
  }


  window.loadMeetings = loadMeetings;
  window.loadMembers = loadMembers;
  window.loadAttendance = loadAttendance;
  window.deleteMeeting = deleteMeeting;
  window.deleteMember = deleteMember;
  window.downloadCSV = downloadCSV;
  
});
