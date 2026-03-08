// Protect Route Strictly via Server Validation
async function verifySession() {
    const token = localStorage.getItem('authToken');
    if (window.location.pathname.endsWith('stress2.html')) {
        if (!token) {
            window.location.href = 'login.html';
            return;
        }

        try {
            const response = await fetch('/api/auth/verify', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'ngrok-skip-browser-warning': '69420'
                }
            });
            const data = await response.json();
            if (!data.success) {
                logoutUser();
            }
        } catch (error) {
            console.log("Auth verification error:", error);
        }
    }
}
verifySession();

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
        "Healthy_Diet": parseInt(document.getElementById("healthy_diet").value) || 5,
        "Fast_Food_Weekly": parseInt(document.getElementById("fast_food").value) || 0,
        "Health_Issues": parseInt(document.getElementById("health_issues").value) || 0,
        "Location_Type": document.getElementById("location_type").value,
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
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                'ngrok-skip-browser-warning': '69420'
            },
            body: JSON.stringify(input_data)
        });

        const apiData = await response.json();

        if (apiData.success) {
            const stress_level = apiData.stress_level;
            const suggestions_list = apiData.suggestions;

            // Format output based on new 5-tier ML prediction
            if (stress_level === "Minimal") {
                result.innerHTML = "🌱 Minimal Stress Level";
                result.className = "minimal-stress";
                suggestion.className = "minimal-stress";
            } else if (stress_level === "Mild") {
                result.innerHTML = "😊 Mild Stress Level";
                result.className = "mild-stress";
                suggestion.className = "mild-stress";
            } else if (stress_level === "Moderate") {
                result.innerHTML = "😐 Moderate Stress Level";
                result.className = "moderate-stress";
                suggestion.className = "moderate-stress";
            } else if (stress_level === "High") {
                result.innerHTML = "⚠ High Stress Level";
                result.className = "high-stress";
                suggestion.className = "high-stress";
            } else if (stress_level === "Critical") {
                result.innerHTML = "🚨 CRITICAL STRESS LEVEL";
                result.className = "critical-stress";
                suggestion.className = "critical-stress";
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

    // Initialize jsPDF
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    // Set Document Properties
    doc.setProperties({
        title: 'Stress Health Report',
        subject: 'Predictive Health Analytics',
        author: 'Vishal Ghasoliya System'
    });

    // Brand Header
    doc.setFont("helvetica", "bold");
    doc.setFontSize(22);
    doc.setTextColor(34, 47, 62); // Dark slate
    doc.text("STRESS HEALTH MONITOR REPORT", 20, 20);

    // Sub Header Divider
    doc.setLineWidth(0.5);
    doc.setDrawColor(200, 200, 200);
    doc.line(20, 25, 190, 25);

    // Parse the raw text we saved into structured data for the PDF
    const reportLines = window.latestReportText.split('\n');
    let yOffset = 35;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(12);
    doc.setTextColor(50, 50, 50);

    // Iterate through lines to print, adding logic for "Suggestions" and bolding
    reportLines.forEach(line => {
        // Skip empty or purely decorative lines
        if (line === "--- STRESS HEALTH REPORT ---" || line.trim() === "") return;

        // Highlight Prediction
        if (line.startsWith("Prediction:")) {
            yOffset += 5;
            doc.setFont("helvetica", "bold");
            doc.setFontSize(14);
            if (line.includes("High")) doc.setTextColor(231, 76, 60); // Red
            else if (line.includes("Medium")) doc.setTextColor(243, 156, 18); // Orange
            else doc.setTextColor(46, 204, 113); // Green

            doc.text(line, 20, yOffset);
            doc.setTextColor(50, 50, 50); // Reset color
            doc.setFont("helvetica", "normal");
            doc.setFontSize(12);
            yOffset += 10;
        }
        // Subheaders
        else if (line === "Suggestions:") {
            yOffset += 10;
            doc.setFont("helvetica", "bold");
            doc.setFontSize(16);
            doc.text("Personalized Action Plan:", 20, yOffset);
            doc.setFont("helvetica", "normal");
            doc.setFontSize(12);
            yOffset += 8;
        }
        else if (line.includes("Thank you for using")) {
            yOffset += 15;
            doc.setFont("helvetica", "italic");
            doc.setFontSize(10);
            doc.setTextColor(150, 150, 150);
            doc.text(line, 20, yOffset);
            doc.setTextColor(50, 50, 50);
        }
        // Standard text lines and wrapped suggestions
        else {
            // Split long text into multiple lines so it doesn't overflow the PDF page edge
            const splitLines = doc.splitTextToSize(line, 170);
            doc.text(splitLines, 20, yOffset);
            yOffset += (splitLines.length * 7);
        }
    });

    // Trigger PDF browser download
    doc.save(`Stress_Health_Report_${new Date().getTime()}.pdf`);
}

function logoutUser() {
    localStorage.removeItem('userEmail');
    localStorage.removeItem('authToken');
    window.location.href = 'login.html';
}