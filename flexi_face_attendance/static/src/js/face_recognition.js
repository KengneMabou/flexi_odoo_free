/** @odoo-module **/
import kiosk from "@hr_attendance/public_kiosk/public_kiosk_app";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
const MODEL_URL = '/flexi_face_attendance/static/src/js/weights';
faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL)
faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL)
faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL)
faceapi.nets.tinyFaceDetector.load(MODEL_URL),
faceapi.nets.faceLandmark68TinyNet.load(MODEL_URL),
faceapi.nets.faceExpressionNet.load(MODEL_URL),
faceapi.nets.ageGenderNet.load(MODEL_URL)

patch(kiosk.kioskAttendanceApp.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.employee_image = useRef("employee_image");
        this.video = useRef("video");
        this.notification = useService("notification");
        this.state.employee = false;
        this.state.verifiedEmployeeId = null;
        this.isRecognitionActive = false;
        this.currentStream = null;
        this.faceMatcher = null;
        this.noMatchCount = 0;
        this.liveness = 0;
        this.lastFacialExpression = "neutral";
        this.geoservice = null;
    },
    async getCurrentFaceExpression(expressionsBundle) {
        var faceValue = "neutral";
        if(expressionsBundle){
            const FACIAL_EXPRESSIONS = ['neutral', 'happy', 'sad', 'angry', 'fearful', 'disgusted', 'surprised'];

            var faceProba = 0;
            for(var facialName in FACIAL_EXPRESSIONS) {
                if(expressionsBundle[facialName] > faceProba){
                    faceValue = facialName;
                    faceProba = expressionsBundle[facialName];
                }
            }
        }
        return faceValue;
    },

    async getGeolocationPosition(employeeId) {
        self = this;
        if (navigator && navigator.geolocation){
            try {
                if(!this.geoservice){
                    this.geoservice = navigator.geolocation;
                }
                const geoOptions = {
                    maximumAge: 0,
                    timeout: Infinity,
                    enableHighAccuracy: true,
                };
                const positionWatchID = this.geoservice.getCurrentPosition(async (locPosition) => {
                    //clear position watch
                    self.geoservice.clearWatch(positionWatchID);
                    // set employee last location
                    await self.rpc("/set_employee_location", {
                        employee_id: employeeId,
                        latitude: locPosition.coords.latitude,
                        longitude: locPosition.coords.longitude,
                    });
                    // start webcam
                    await self.startWebcam();
                }, async (locError) => {
                    console.error("Error watching geoposition: ", locError);
                    self.notification.add(_t("Your browser encounterer an error while watching geoposition: " + locError.message), {
                        title : "Access Denied !",
                        type: "danger",
                    });
                }, geoOptions);

            } catch (navError) {
                console.error("Error getting geoposition:", navError);
                this.notification.add(_t("Your browser does not retrieve geoposition. Please try a different browser."), {
                    title : "Access Denied !",
                    type: "danger",
                });
            }

        }
        else{
            console.error("Error starting geolocation:", error);
            this.notification.add(_t("Your browser does not support geolocation service. Please try a different browser."), {
                title : "Access Denied !",
                type: "danger",
            });
        }
    },

    async loadImage(employeeId) {
        var image = await this.rpc("/get_image", {
            employee_id: employeeId
        });
        this.have_image = image;
        const employee_image = this.employee_image.el;
        employee_image.src = "data:image/jpeg;base64," + image;
        this.currentVerificationId = employeeId;
    },

    async startWebcam() {
        const video = this.video.el;
        if (video) {
            video.srcObject = null;
            video.style.display = 'block';
        }
        this.isRecognitionActive = true;
        this.state.employee = false;
        this.noMatchCount = 0; // Reset no match counter
        this.faceMatcher = null; // Reset faceMatcher
        this.liveness = 0; // reset liveness

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });
            this.currentStream = stream;
            video.srcObject = stream;
            await new Promise(resolve => {
                video.onloadedmetadata = resolve;
            });
            await this.faceRecognition(video);
        } catch (error) {
            console.error("Error starting webcam:", error);
            this.isRecognitionActive = false;
            this.notification.add(_t("Your browser does not support camera access. Please try a different browser."), {
                title : "Access Denied !",
                type: "danger",
            });
        }
    },

    async getLabeledFaceDescriptions() {
        const employee_image = this.employee_image.el;
        const detections = await faceapi
            .detectSingleFace(employee_image)
            .withFaceLandmarks()
            .withFaceExpressions()
            .withFaceDescriptor();
        return detections;
    },

    stopRecognition(video, canvas) {
        this.isRecognitionActive = false;
        if (this.currentStream) {
            this.currentStream.getTracks().forEach(track => track.stop());
            this.currentStream = null;
        }
        if (video) {
            video.srcObject = null;
            video.style.display = 'none';
        }
        if (canvas && canvas.parentNode) {
            canvas.remove();
        }
        const modal = document.getElementById('WebCamModal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.faceMatcher = null;
        this.noMatchCount = 0;
        this.liveness = 0;
    },

    async faceRecognition(video) {
        if (!this.isRecognitionActive) return;
        if (!this.faceMatcher) {
            const labeledFaceDescriptors = await this.getLabeledFaceDescriptions();
            if (labeledFaceDescriptors && labeledFaceDescriptors.descriptor) {
                this.faceMatcher = new faceapi.FaceMatcher([labeledFaceDescriptors.descriptor]);
            } else {
                console.error("Could not get face descriptor from reference image");
                this.notification.add(_t("Failed to initialize face recognition, Please upload a new, properly formatted image."), {
                    type: "danger",
                    title: "Image detection failed!",
                });
                this.stopRecognition(video);
                return;
            }
        }
        const canvas = faceapi.createCanvasFromMedia(video);
        document.body.append(canvas);
        canvas.style.display = 'none'
        const displaySize = { width: video.videoWidth, height: video.videoHeight };
        faceapi.matchDimensions(canvas, displaySize);
        const processFrame = async () => {
            if (!this.isRecognitionActive) return;
            try {
                const detections = await faceapi
                    .detectAllFaces(video)
                    .withFaceLandmarks()
                    .withFaceExpressions()
                    .withFaceDescriptors();
                if (detections.length === 0) {
                    if (this.isRecognitionActive) {
                        requestAnimationFrame(processFrame);
                    }
                    return;
                }
                console.error("Face detections object: ", detections);
                if(this.liveness >= 3){
                    for (const detection of detections) {
                        const match = this.faceMatcher.findBestMatch(detection.descriptor);
                        if (match._distance < 0.4) {
                            this.state.employee = true;
                            this.state.verifiedEmployeeId = this.currentVerificationId;
                            this.stopRecognition(video, canvas);
                            return;
                        } else {
                            this.noMatchCount++;
                            if (this.noMatchCount >= 3) {
                                this.notification.add(_t("Sorry, cannot recognize you"), {
                                    title:"Recognition Failed ! ",
                                    type: "danger",
                                });
                                this.stopRecognition(video, canvas);
                                return;
                            }
                        }
                    }
                    if (this.isRecognitionActive) {
                        requestAnimationFrame(processFrame);
                    }
                }
                else{
                    for (const detection of detections) {
                        if (this.getCurrentFaceExpression(detections.expressions) != this.lastFacialExpression){
                            this.liveness++;
                            if (this.isRecognitionActive) {
                                requestAnimationFrame(processFrame);
                            }
                        }
                    }
                }
            } catch (error) {
                console.error("Face recognition error:", error);
                this.stopRecognition(video, canvas);
            }
        };
        processFrame();
    },

    async onManualSelection(employeeId, enteredPin) {
        if (this.isRecognitionActive) {
            this.stopRecognition(this.video.el);
        }
        await this.loadImage(employeeId);
        await this.getGeolocationPosition(employeeId);
        if(!this.geoservice){
            this.notification.add(_t("Sorry, we cannot geolocate you"), {
                                    title:"Attendance Failed ! ",
                                    type: "danger",
                                });
            return;
        }

        if (this.have_image) {
            const modal = document.getElementById('WebCamModal');
            if (modal) {
                modal.style.display = 'block';
            }
            const checkInterval = setInterval(() => {
                if (this.state.employee && this.state.verifiedEmployeeId === employeeId) {
                    clearInterval(checkInterval);
                    this.rpc("manual_selection", {
                        token: this.props.token,
                        employee_id: employeeId,
                        pin_code: enteredPin,
                    }).then(result => {
                        if (result && result.attendance) {
                            this.employeeData = result;
                            this.switchDisplay("greet");
                        } else {
                            if (enteredPin) {
                                this.notification.add(_t("Wrong Pin"), {
                                    type: "danger",
                                });
                            }
                        }
                    });
                }
            }, 500);
        } else {
            await this.notification.add(_t("Selected cashier has no image."), {
                title: _t("Authentication failed"),
                type: "danger",
            });
            location.reload();
        }
    },
});