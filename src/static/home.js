var stop = $('#stop_form');
stop.submit(function (e) {
    e.preventDefault()
    $.ajax({
        type: 'POST',
        url: window.location.href,
        data: {
            command: "stop",
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
        },
        success: function (data) {
            console.log(data.msg);
        }
    });
    return false;
});

var start = $('#start_form');
start.submit(function (e) {
    e.preventDefault()
    $.ajax({
        type: 'POST',
        url: window.location.href,
        data: {
            command: "start",
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
        },
        success: function (data) {
            console.log(data.msg);
        }
    });
    return false;
});

// create an ajax get request that gets the momentary data in the success response
function updatePageData() {
    $.ajax({
        type: 'GET',
        url: window.location.href,
        data: {
            command: 'get_page_data',
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
        },
        success: function (data) {
            console.log("UPDATE ACCOUNT DATA");
            console.log(data);

            // Update account Information
            let account_div = document.getElementById("account_div");
            account_div.innerHTML = "";
            data.account.balances.forEach(function (balance) {
                let p = document.createElement("p");
                p.style.fontSize = "20px";
                let b = document.createElement("b");
                b.appendChild(document.createTextNode(`${balance.asset}: `));
                p.appendChild(b)
                p.appendChild(document.createTextNode(`free: ${balance.free},  locked: ${balance.locked}`));
                account_div.appendChild(p);
            });
            let h3 = document.createElement("h3");
            h3.innerText = `Performance: ${data.account.performance}`;
            account_div.appendChild(h3);
        }
    });
}
function updateLogs() {
    $.ajax({
        type: 'GET',
        url: window.location.href,
        data: {
            command: "get_logs",
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
        },
        success: function (data) {
            // Update all logs
            let log_div = document.getElementById("log_div");
            log_div.innerHTML = "";
            log_div.style.fontSize = "20px";
            data.logs.forEach(function (log) {
                let li = document.createElement("li");
                li.appendChild(document.createTextNode(`${log.time}: ${log.message}`));
                log_div.appendChild(li);
            });
        }
    });
}


// The following code creates a worker, that creates a frequency to update the frontend data
// Hacker method to enable webworker in chrome
function getScriptPath(foo) {
    return window.URL.createObjectURL(new Blob([foo.toString().match(/^\s*function\s*\(\s*\)\s*\{(([\s\S](?!\}$))*[\s\S])/)[1]], {type: 'text/javascript'}));
}

// Create a clock that requests an update every 60 seconds
var data_clock = new Worker(getScriptPath(function () {
    var running = false;
    var stepTime = 30000;

    function run() {
        if (running) {
            postMessage({msg: "UPDATE DATA"});
            setTimeout(run, stepTime);
        }
    }

    self.addEventListener('message', function (e) {
        running = true;
        run();
    });
}));
// Define what to do once the worker sends a message
data_clock.onmessage = function (e) {
    updatePageData();
};
// Send a message to the worker to start creating the frequency
data_clock.postMessage({msg: 'START data_clock'});


// Create a clock that requests an update every second
var log_clock = new Worker(getScriptPath(function () {
    var running = false;
    var stepTime = 1000;

    function run() {
        if (running) {
            postMessage({msg: "UPDATE LOGS"});
            setTimeout(run, stepTime);
        }
    }

    self.addEventListener('message', function (e) {
        running = true;
        run();
    });
}));
// Define what to do once the worker sends a message
log_clock.onmessage = function (e) {
    updateLogs();
};
// Send a message to the worker to start creating the frequency
log_clock.postMessage({msg: 'START log_clock'});

console.log("All workers started")