; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9e3f9aab_attacker_service_has_many_slots () Bool)
(declare-fun c9e3f9aab_operator_address_used_as_instance () Bool)
(declare-fun c9e3f9aab_operator_permanently_blocked_from_registering () Bool)
(declare-fun c9e3f9aab_operator_registered_instance_count () Int)
(declare-fun c9e3f9aab_service_in_active_registration () Bool)
(declare-fun c9e3f9aab_victim_is_operator_address () Bool)
(assert
 (= c9e3f9aab_attacker_service_has_many_slots c9e3f9aab_attacker_service_has_many_slots))
(assert
 (= c9e3f9aab_operator_address_used_as_instance c9e3f9aab_operator_address_used_as_instance))
(assert
 (= c9e3f9aab_operator_permanently_blocked_from_registering c9e3f9aab_operator_permanently_blocked_from_registering))
(assert
 (= c9e3f9aab_operator_registered_instance_count c9e3f9aab_operator_registered_instance_count))
(assert
 (= c9e3f9aab_service_in_active_registration c9e3f9aab_service_in_active_registration))
(assert
 (= c9e3f9aab_victim_is_operator_address c9e3f9aab_victim_is_operator_address))
(define-fun report_preconditions () Bool (and c9e3f9aab_attacker_service_has_many_slots
     c9e3f9aab_service_in_active_registration
     c9e3f9aab_victim_is_operator_address))
(define-fun report_safety () Bool (=> c9e3f9aab_operator_address_used_as_instance
    (= 0 c9e3f9aab_operator_registered_instance_count)))
(define-fun report_effects () Bool (and c9e3f9aab_operator_address_used_as_instance
     (not (= 0 c9e3f9aab_operator_registered_instance_count))
     c9e3f9aab_operator_permanently_blocked_from_registering
     c9e3f9aab_operator_permanently_blocked_from_registering))
