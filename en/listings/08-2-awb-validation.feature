# Listing from Section 8.5.1 of the textbook “Fundamentals of Business Process Analysis and Modelling in IT”.

Feature: Automatic validation of e-AWB data

  Scenario: Error in the check digit of the air waybill number
    Given the freight forwarder has sent a booking with AWB number "176-12345674"
    When the system validates the e-AWB data
    Then the booking gets the state "Needs correction"
    And a message with the error "invalid check digit" is sent to the freight forwarder
    And the delivery slot is not confirmed

  Scenario: Correct data
    Given the freight forwarder has sent a booking with AWB number "176-12345675" and complete data
    When the system validates the e-AWB data
    Then the booking gets the state "Confirmed"
    And the freight forwarder is offered free delivery slots
