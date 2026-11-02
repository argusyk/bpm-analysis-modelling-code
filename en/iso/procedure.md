# Procedure "Acceptance and handling of an export shipment (to-be)"

The draft was generated automatically from the BPMN model; it is reviewed by the process owner before approval.

## 1. Purpose and scope

The procedure establishes how the process "Acceptance and handling of an export shipment (to-be)" is performed. The process starts with the event "Booking with e-AWB received" and ends with the events: "Shipment handed over to carrier".

## 2. Participants (roles)

- Commercial department
- Documentation service
- Export warehouse
- ULD team

## 3. Procedure

1. Validate e-AWB. Performer: Commercial department; performed automatically by rules.
   Decision: Data correct? "no" – go to "Request correction"; "yes" – go to "Confirm delivery slot".
2. Request correction. Performer: Documentation service; sending a message.
3. Confirm delivery slot. Performer: Commercial department; sending a message.
   Waiting for the event: "Correction received".
   Waiting for the event: "Cargo delivered".
4. Accept cargo. Performer: Export warehouse; performed by an employee in the information system.
   The following steps are performed in parallel: "Pass screening", "Obtain customs release".
5. Pass screening. Performer: Export warehouse; performed by an employee in the information system.
6. Obtain customs release. Performer: Documentation service; performed by an employee in the information system.
7. Hand over ULD. Performer: ULD team; performed manually.

## 4. Records (retained documented information)

- the event log of process instances with timestamps and performers;
- the results of checks and decisions at each gateway;
- messages sent to external participants.

## 5. Process indicators

The indicators and target values are defined in the process passport (Appendix F, Table F.1).
