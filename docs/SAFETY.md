# Safety and ethical use

## Prototype status

JØ7 VIREO is a research and educational prototype. It has not been certified as a medical device, mobility aid, personal protective device or collision-avoidance system.

## Never rely on VIREO alone

A user should continue using appropriate mobility support, which may include a white cane, guide dog, formal orientation and mobility training, trained human guidance or other certified aids. VIREO can miss objects, misclassify scenes, delay announcements or stop because of power, camera, software or environmental faults.

## Known perception risks

- very low illumination;
- direct glare and reflective surfaces;
- patterned backgrounds;
- objects closer than approximately 15–20 cm in the report's visual tests;
- occluded or small objects;
- classes absent or underrepresented in training data;
- audio flooding or overwritten announcements;
- speech-recognition errors;
- camera movement that changes the observed field without the user's awareness.

## Human testing

The source report explicitly notes that the project was still a prototype and had not yet been tested on a visually impaired person at that stage. Any future user study requires informed consent, accessible instructions, risk assessment, supervision, a safe controlled environment, a withdrawal process and appropriate ethics approval.

## Haptic belt

- Never drive motors directly from microcontroller GPIO.
- Prevent exposed wiring or hot components from contacting skin.
- Limit vibration intensity and continuous duty cycle.
- Provide a physical power disconnect.
- Test sensor failure modes before wearing the belt.
- Do not interpret the three-zone belt as full spatial coverage.

## Servo

- Use mechanical end stops and software angle limits.
- Avoid hair, clothing and cable pinch points.
- Use a stable external supply when required.
- Confirm that the servo cannot pull the camera cable or enclosure into the user.

## Batteries

The prototype used reclaimed vape cells. Reclaimed lithium-ion cells may be damaged, mismatched or unsafe. The public repository does not recommend reconstructing that pack. Use certified cells, qualified pack assembly, a correctly rated BMS and fuse, and professional electrical review.

## Local language model

Optional Ollama responses are probabilistic and may be wrong. They must not be used for emergency, medical, navigation or survival decisions. Core hazard feedback should remain deterministic and independent of the language model.

## Privacy

The intended design performs camera and speech processing locally. Users should still be informed when cameras and microphones are active, and recordings should not be stored without explicit consent.
