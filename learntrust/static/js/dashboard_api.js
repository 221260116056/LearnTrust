fetch("/api/dashboard/")
.then(response => response.json())
.then(data => {

    document.getElementById("welcome").innerText = data.welcome;
    document.getElementById("totalCourses").innerText = data.total_courses;
    document.getElementById("completedModules").innerText = data.completed_modules;

})
.catch(error => console.log(error));
