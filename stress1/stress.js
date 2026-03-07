async function detectStress() {

    // Disable button to prevent spam
    const btn = document.querySelector('button[type="submit"]');
    btn.innerText = "Analyzing...";
    btn.disabled = true;

    // Build the payload mapping perfectly to the Python ML script expectations
    const input_data = {
        "Age": parseInt(document.getElementById("age").value) || 0,
        "Weight": parseFloat(document.getElementById("weight").value) || 0,
        "Sleep_Hours": parseFloat(document.getElementById("sleep").value) || 0,
        "Sleep_Timing": document.getElementById("sleep_timing").value,
        "Working_Hours": parseFloat(document.getElementById("work").value) || 0,
        "Study_Hours": parseFloat(document.getElementById("study").value) || 0,
        "Exercise_Hours": parseFloat(document.getElementById("exercise").value) || 0,
        "Water_Intake": parseInt(document.getElementById("water").value) || 0,
        "Exam_Preparation": parseInt(document.getElementById("exam_prep").value) || 0,
        "Family_Issues": parseInt(document.getElementById("family_issues").value) || 0,
        "Social_Media_Usage": parseInt(document.getElementById("social_media").value) || 0,
        "Instagram_Hours": parseFloat(document.getElementById("instagram").value) || 0,
        "Facebook_Hours": parseFloat(document.getElementById("facebook").value) || 0,
        "email": localStorage.getItem("userEmail") || "anonymous" // For MongoDB tagging
    };

    if (input_data.Social_Media_Usage === 0) {
        input_data.Instagram_Hours = 0;
        input_data.Facebook_Hours = 0;
    }

    let result = document.getElementById("result");
    let suggestion = document.getElementById("suggestion");

    try {
        // Send data to Flask Backend
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': '69420'
            },
            body: JSON.stringify(input_data)
        });

        const apiData = await response.json();

        if (apiData.success) {
            const stress_level = apiData.stress_level;
            const suggestions_list = apiData.suggestions;

            // Format output based on ML prediction
            if (stress_level === "High") {
                result.innerHTML = "⚠ High Stress Level";
                result.className = "high-stress";
                suggestion.className = "high-stress";
            } else if (stress_level === "Medium") {
                result.innerHTML = "😐 Medium Stress Level";
                result.className = "medium-stress";
                suggestion.className = "medium-stress";
            } else {
                result.innerHTML = "😊 Healthy Stress Level";
                result.className = "low-stress";
                suggestion.className = "low-stress";
            }

            // Render Suggestions 
            let html_suggestions = "<h3>Suggestions</h3><ul>";
            suggestions_list.forEach(sug => {
                html_suggestions += `<li>${sug}</li>`;
            });
            html_suggestions += "</ul>";

            // Add a small database confirmation stamp
            html_suggestions += `<p style="font-size: 12px; color: #7f8c8d; margin-top: 15px;">💾 Report securely saved to MongoDB database.</p>`;

            suggestion.innerHTML = html_suggestions;

            // Show the download button
            document.getElementById('actionButtons').style.display = 'flex';

            // Save the raw text response for the download button
            let reportText = `--- STRESS HEALTH REPORT ---\n`;
            reportText += `User: ${input_data.email}\n`;
            reportText += `Date: ${new Date().toLocaleString()}\n\n`;
            reportText += `Prediction: ${stress_level} Stress Level\n\n`;
            reportText += `Suggestions:\n`;
            suggestions_list.forEach(sug => {
                reportText += `- ${sug}\n`;
            });
            reportText += `\nThank you for using the Stress Health Monitor created by VISHAL GHASOLIYA.`;

            window.latestReportText = reportText;

        } else {
            result.innerHTML = "❌ Error: Could not generate report.";
            suggestion.innerHTML = `<p>${apiData.error}</p>`;
        }

    } catch (error) {
        console.log(error);
        result.innerHTML = "❌ ma ka bosra aag";
        suggestion.innerHTML = "<p>Could not connect to the Python Backend. Make sure app.py is running!</p>";
    } finally {
        // Re-enable button
        btn.innerText = "Check Stress Level";
        btn.disabled = false;
    }
}

function downloadReport() {
    if (!window.latestReportText) {
        alert("No report generated yet to download.");
        return;
    }

    // Create a blob from the text
    const blob = new Blob([window.latestReportText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);

    // Create a temporary anchor to trigger download
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Stress_Health_Report.txt';
    document.body.appendChild(a);
    a.click();

    // Cleanup
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function logoutUser() {
    localStorage.removeItem('userEmail');
    window.location.href = 'login.html';
}