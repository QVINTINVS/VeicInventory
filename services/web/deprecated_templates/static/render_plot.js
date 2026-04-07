const delayRange = document.getElementById("delayRange")
const btPreviousFrame = document.getElementById("bt-previous-frame")
const btNextFrame = document.getElementById("bt-next-frame")
const frameLabel = document.getElementById("frame-label")
let currentFrame = 0
let isPaused = false
let isCycle = true
let lastFrame
let frames = []
let targetVars
let selectedVar = "CO2_BIO"
let altitude = 0
let intervalId = null
let delay = parseInt(delayRange.value)
let alts_length

async function fetchAndPlotHeatmap() {
    try {
        // Fetch the data from the Flask backend

        if (intervalId) {
            clearInterval(intervalId)
        }
        intervalId = null

        const response = await fetch(`/get_netcdf_data${selectedVar ? `?data_variable=${selectedVar}` : ''}&altitude=${altitude}`);
        const data = await response.json();

        // Extract data from the JSON response
        const lats = data.lats
        const lons = data.lons
        const description = data.description
        const units = data.units
        const zmin = data.zmin
        const zmax = data.zmax
        // const time = data.time
        alts_length = data.alts_length
        frames = data.frames
        targetVars = data.target_vars || []
        lastFrame = frames.length

        // Initialize the heatmap with the first frame
        const initialFrame = frames[0];

        // Prepare Plotly data
        const plotData = [
            {
                z: initialFrame, // First time step's data
                x: lons[0], // Longitude grid
                y: lats.map(row => row[0]), // Latitude grid
                type: 'heatmap',
                colorscale: 'Viridis',
                zmin: zmin,
                zmax: zmax,
                colorbar: {
                    title: `${description} (${units})`
                }
            }
        ];

        // Prepare layout
        const layout = {
            title: `${description} (altitude: ${altitude})`,
            xaxis: {
                title: 'Longitude'
            },
            yaxis: {
                title: 'Latitude'
            },
            plot_bgcolor: "#f8f9fa",
            paper_bgcolor: "#f8f9fa",
        };

        // Initialize the heatmap
        Plotly.newPlot('heatmap', plotData, layout);

        // Animate through frames
        intervalId = setInterval(() => {
            const frameData = frames[currentFrame + 1]

            // Update the heatmap with new frame data
            Plotly.update('heatmap', {
                z: [frameData] // Update heatmap data
            });

            
            if (currentFrame + 1 === frames.length && (!isPaused || isCycle)) {
                console.log("got here lol")
                // document.body.dispatchEvent(new KeyboardEvent(("keydown", { code: "Space" })))
                isPaused = !isPaused
            }
            if (isPaused) {
                return
            }
            
            currentFrame = (currentFrame + 1) % frames.length; // Loop through frames
            console.log(`currentFrame: ${currentFrame}`)
            frameLabel.textContent = `Frame: ${currentFrame}`

        }, delay)
    } catch (error) {
        console.error('Error fetching or plotting NetCDF data:', error);
    }

    const dropdownMenu = document.getElementById("dropdownMenu")

    dropdownMenu.innerHTML = ""
    if (targetVars && Array.isArray(targetVars)) {
        targetVars.forEach(key => {
            const item = document.createElement("li")
            item.innerHTML = `<a class="dropdown-item" href="#">${key.trim()}</a>`

            item.querySelector("a").addEventListener("click", () => {
                updateSelectedVar(key.trim())
            })

            dropdownMenu.appendChild(item)
        })
    }
}

// let iframe = document.getElementById("body")
document.body.addEventListener("keydown", (e) => {
    // e.preventDefault()
    // handleKeyDown(e)
    console.log(e.code)
    if (e.code === "Space") {
        e.preventDefault()
        isPaused = !isPaused
        console.log("isPaused:", isPaused)
        console.log("currentFrame:", currentFrame)

        if (!isPaused && currentFrame + 1 === lastFrame) {
            currentFrame = 0
            isPaused = false
        }

    }

    if (e.code === "ArrowLeft") {
        // (currentFrame > 0) ? currentFrame-- : currentFrame = 0
        // console.log("currentFrame:", currentFrame)
        btPreviousFrame.click()
    }

    if (e.code === "ArrowRight") {
        // (currentFrame < lastFrame) ? currentFrame++ : currentFrame = lastFrame
        // console.log("currentFrame:", currentFrame)
        btNextFrame.click()
    }

    if (e.code === "KeyC") {
        isCycle = !isCycle
        console.log(`isCycle: ${isCycle}`)
    }

    if (e.code === "ArrowDown") {
        e.preventDefault()
        if (altitude > 0) updateAltitude(altitude-1)
        console.log(`altitude: ${altitude}`)
    }

    if (e.code === "ArrowUp") {
        e.preventDefault()
        if (altitude+1 < alts_length) updateAltitude(altitude+1)
        console.log(`altitude: ${altitude}`)
    }
})

delayRange.addEventListener("input", function () {
    delay = parseInt(this.value);
    document.getElementById("delayValue").textContent = `${delay} ms`;

    if (intervalId) {
        clearInterval(intervalId);
    }

    intervalId = setInterval(() => {
        const frameData = frames[currentFrame + 1]

        // Update the heatmap with new frame data
        Plotly.update('heatmap', {
            z: [frameData] // Update heatmap data
        });
        if (currentFrame + 1 === frames.length && (!isPaused || isCycle)) {
            console.log("got here lol")
            // document.body.dispatchEvent(new KeyboardEvent(("keydown", { code: "Space" })))
            isPaused = !isPaused
        }
        if (isPaused) {
            return
        }

        currentFrame = (currentFrame + 1) % frames.length; // Loop through frames
        console.log(`currentFrame: ${currentFrame}`)
        frameLabel.textContent = `Frame: ${currentFrame}`

    }, delay)

})

btPreviousFrame.addEventListener("click", (e) => {
    (currentFrame > 0) ? currentFrame-- : currentFrame = 0
    console.log("currentFrame:", currentFrame)
    frameLabel.textContent = `Frame: ${currentFrame}`
})

btNextFrame.addEventListener("click", (e) => {
    (currentFrame < lastFrame) ? currentFrame++ : currentFrame = lastFrame
    console.log("currentFrame:", currentFrame)
    frameLabel.textContent = `Frame: ${currentFrame}`
})

fetchAndPlotHeatmap()

$(document).ready(function () {
    $('#visualizeModal').on('hidden.bs.modal', function () {
        $('#iframeId').attr('src', $('#iframeId').attr('src'))
        isPaused = true
    })

    $('#visualizeModal').on('shown.bs.modal', function () {
        isPaused = false
    })
})

function updateSelectedVar(newVar) {
    selectedVar = newVar
    console.log(`selectedVar changed to: ${selectedVar}`)
    fetchAndPlotHeatmap() // Fetch new data and update the plot
}

function updateAltitude(newAltitude) {
    altitude = newAltitude
    console.log(`altitude changed to: ${altitude}`)
    fetchAndPlotHeatmap() // Fetch new data and update the plot
}

function getVariables() {
    return targetVars
}

