; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2c8b9261_multi_service_registration_broken () Bool)
(declare-fun c2c8b9261_operator_registers_instances_many_services () Bool)
(declare-fun c2c8b9261_victim_is_operator () Bool)
(assert
 (= c2c8b9261_multi_service_registration_broken c2c8b9261_multi_service_registration_broken))
(assert
 (= c2c8b9261_operator_registers_instances_many_services c2c8b9261_operator_registers_instances_many_services))
(assert
 (= c2c8b9261_victim_is_operator c2c8b9261_victim_is_operator))
(define-fun report_preconditions () Bool c2c8b9261_victim_is_operator)
(define-fun report_safety () Bool (=> c2c8b9261_victim_is_operator
    c2c8b9261_operator_registers_instances_many_services))
(define-fun report_effects () Bool (and c2c8b9261_victim_is_operator
     (not c2c8b9261_operator_registers_instances_many_services)
     c2c8b9261_multi_service_registration_broken))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
