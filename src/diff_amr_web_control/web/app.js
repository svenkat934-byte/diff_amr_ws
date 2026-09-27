// Connect to ROS 2 through rosbridge
const ros = new ROSLIB.Ros({
    url: "ws://localhost:9090"
});

const statusElement = document.getElementById("status");

let connected = false;
let linear = 0.0;
let angular = 0.0;

// ROS connection events
ros.on("connection", function () {
    connected = true;
    statusElement.textContent = "Connected to ROS 2";
    statusElement.style.color = "#4ade80";
});

ros.on("error", function (error) {
    console.error("ROS connection error:", error);
    statusElement.textContent = "ROS connection error";
    statusElement.style.color = "#f87171";
});

ros.on("close", function () {
    connected = false;
    linear = 0.0;
    angular = 0.0;

    statusElement.textContent = "Disconnected from ROS 2";
    statusElement.style.color = "#f87171";
});

// Create velocity publisher
const cmdVel = new ROSLIB.Topic({
    ros: ros,
    name: "/wheel_controller/cmd_vel",
    messageType: "geometry_msgs/msg/TwistStamped"
});

// Speed settings
const linearSlider = document.getElementById("linearSpeed");
const angularSlider = document.getElementById("angularSpeed");

const linearValue = document.getElementById("linearValue");
const angularValue = document.getElementById("angularValue");

linearSlider.addEventListener("input", function () {
    linearValue.textContent = Number(this.value).toFixed(2);
});

angularSlider.addEventListener("input", function () {
    angularValue.textContent = Number(this.value).toFixed(2);
});

// Publish velocity command
function publishVelocity() {
    if (!connected) return;

    const message = new ROSLIB.Message({
        header: {
            stamp: {
                sec: 0,
                nanosec: 0
            },
            frame_id: "base_link"
        },
        twist: {
            linear: {
                x: linear,
                y: 0.0,
                z: 0.0
            },
            angular: {
                x: 0.0,
                y: 0.0,
                z: angular
            }
        }
    });

    cmdVel.publish(message);
}

// Direction controls
function setMovement(direction) {
    const speed = Number(linearSlider.value);
    const turnSpeed = Number(angularSlider.value);

    linear = 0.0;
    angular = 0.0;

    if (direction === "forward") {
        linear = speed;
    }

    if (direction === "backward") {
        linear = -speed;
    }

    if (direction === "left") {
        angular = turnSpeed;
    }

    if (direction === "right") {
        angular = -turnSpeed;
    }

    publishVelocity();
}

function stopRobot() {
    linear = 0.0;
    angular = 0.0;

    publishVelocity();
}

// Hold-to-move controls
function setupButton(id, direction) {
    const button = document.getElementById(id);

    button.addEventListener("pointerdown", function (event) {
        event.preventDefault();
        button.setPointerCapture(event.pointerId);
        setMovement(direction);
    });

    button.addEventListener("pointerup", stopRobot);
    button.addEventListener("pointercancel", stopRobot);
    button.addEventListener("lostpointercapture", stopRobot);
}

setupButton("forward", "forward");
setupButton("backward", "backward");
setupButton("left", "left");
setupButton("right", "right");

document.getElementById("stop").addEventListener(
    "click",
    stopRobot
);

// Publish periodically while a button is held
setInterval(function () {
    if (connected && (linear !== 0.0 || angular !== 0.0)) {
        publishVelocity();
    }
}, 100);


// --------------------------------
// LIVE CAMERA
// --------------------------------

const cameraFeed = document.getElementById("cameraFeed");
const cameraStatus = document.getElementById("cameraStatus");

const cameraTopic = new ROSLIB.Topic({
    ros: ros,
    name: "/camera/image_raw/compressed",
    messageType: "sensor_msgs/msg/CompressedImage",
    throttle_rate: 100,
    queue_length: 1
});

cameraTopic.subscribe(function (message) {
    if (!message.data) {
        return;
    }

    // CompressedImage data is JPEG/PNG bytes
    // represented as base64 through rosbridge.
    cameraFeed.src =
        "data:image/jpeg;base64," + message.data;

    cameraStatus.textContent = "Camera stream receiving";
    cameraStatus.style.color = "#4ade80";
});

cameraFeed.onerror = function () {
    cameraStatus.textContent = "Unable to decode camera image";
    cameraStatus.style.color = "#f87171";
};


// ==========================================
// LIVE 2D LIDAR VISUALIZATION
// ==========================================

const lidarCanvas = document.getElementById("lidarCanvas");
const lidarCtx = lidarCanvas.getContext("2d");

const lidarStatus = document.getElementById("lidarStatus");
const lidarRange = document.getElementById("lidarRange");

const lidarWidth = lidarCanvas.width;
const lidarHeight = lidarCanvas.height;

// Center of the robot in the visualization
const centerX = lidarWidth / 2;
const centerY = lidarHeight / 2;

// Maximum display range in meters.
// This is a visualization setting, not the sensor's range.
const displayRange = 5.0;

// Pixels per meter
const scale = lidarWidth / (2 * displayRange);

// Subscribe to ROS 2 LaserScan
const scanTopic = new ROSLIB.Topic({
    ros: ros,
    name: "/scan",
    messageType: "sensor_msgs/msg/LaserScan",
    throttle_rate: 100,
    queue_length: 1
});

// Draw the LiDAR background
function drawLidarBackground() {

    lidarCtx.clearRect(
        0,
        0,
        lidarWidth,
        lidarHeight
    );

    lidarCtx.fillStyle = "#020617";

    lidarCtx.fillRect(
        0,
        0,
        lidarWidth,
        lidarHeight
    );

    // Draw range circles
    lidarCtx.strokeStyle = "#334155";
    lidarCtx.lineWidth = 1;

    for (let r = 1; r <= displayRange; r++) {

        const radius = r * scale;

        lidarCtx.beginPath();

        lidarCtx.arc(
            centerX,
            centerY,
            radius,
            0,
            2 * Math.PI
        );

        lidarCtx.stroke();

        // Range labels
        lidarCtx.fillStyle = "#94a3b8";
        lidarCtx.font = "12px Arial";

        lidarCtx.fillText(
            r + "m",
            centerX + 5,
            centerY - radius + 15
        );
    }

    // Horizontal and vertical axes
    lidarCtx.strokeStyle = "#475569";

    lidarCtx.beginPath();

    lidarCtx.moveTo(0, centerY);
    lidarCtx.lineTo(lidarWidth, centerY);

    lidarCtx.moveTo(centerX, 0);
    lidarCtx.lineTo(centerX, lidarHeight);

    lidarCtx.stroke();

    // Robot position
    lidarCtx.fillStyle = "#38bdf8";

    lidarCtx.beginPath();

    lidarCtx.arc(
        centerX,
        centerY,
        7,
        0,
        2 * Math.PI
    );

    lidarCtx.fill();

    // Robot heading indicator (forward)
    lidarCtx.strokeStyle = "#38bdf8";
    lidarCtx.lineWidth = 3;

    lidarCtx.beginPath();

    lidarCtx.moveTo(centerX, centerY);
    lidarCtx.lineTo(centerX, centerY - 25);

    lidarCtx.stroke();
}


// Process each incoming LaserScan message
scanTopic.subscribe(function (scan) {

    drawLidarBackground();

    const ranges = scan.ranges;

    const angleMin = scan.angle_min;
    const angleIncrement = scan.angle_increment;

    const rangeMin = scan.range_min;
    const rangeMax = scan.range_max;

    let validPoints = 0;

    // Convert each range measurement to a 2D point
    for (let i = 0; i < ranges.length; i++) {

        const distance = ranges[i];

        // Ignore invalid or out-of-range measurements
        if (!Number.isFinite(distance)) {
            continue;
        }

        if (distance < rangeMin || distance > rangeMax) {
            continue;
        }

        // Ignore points outside the display radius
        if (distance > displayRange) {
            continue;
        }

        // Angle of this laser measurement
        const angle = angleMin + i * angleIncrement;

        // LaserScan convention:
        // X forward, Y left in the robot frame.
        const x = distance * Math.cos(angle);
        const y = distance * Math.sin(angle);

        // Convert robot coordinates to canvas coordinates.
        // Canvas Y increases downward, so invert Y.
        const canvasX = centerX + x * scale;
        const canvasY = centerY - y * scale;

        // Draw detected obstacle point
        lidarCtx.fillStyle = "#4ade80";

        lidarCtx.beginPath();

        lidarCtx.arc(
            canvasX,
            canvasY,
            2,
            0,
            2 * Math.PI
        );

        lidarCtx.fill();

        validPoints++;
    }

    lidarStatus.textContent =
        "LiDAR connected | Valid points: " + validPoints;

    lidarStatus.style.color = "#4ade80";

    lidarRange.textContent =
        "Sensor range: " +
        rangeMin.toFixed(2) +
        " m - " +
        rangeMax.toFixed(2) +
        " m | Display: " +
        displayRange.toFixed(1) +
        " m";
});

// Initial display
drawLidarBackground();