; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c40cb9fdd_alice_knows_instance_address_flag () Bool)
(declare-fun c40cb9fdd_bob_owns_instance_flag () Bool)
(declare-fun c40cb9fdd_caller_is_designated_operator () Bool)
(declare-fun c40cb9fdd_fake_service_bond_wei () Int)
(declare-fun c40cb9fdd_instance_locked_indefinitely () Bool)
(declare-fun c40cb9fdd_instance_not_yet_registered_flag () Bool)
(declare-fun c40cb9fdd_legitimate_instance_registered () Bool)
(declare-fun c40cb9fdd_register_agents_called () Bool)
(assert
 (= c40cb9fdd_alice_knows_instance_address_flag c40cb9fdd_alice_knows_instance_address_flag))
(assert
 (= c40cb9fdd_bob_owns_instance_flag c40cb9fdd_bob_owns_instance_flag))
(assert
 (= c40cb9fdd_caller_is_designated_operator c40cb9fdd_caller_is_designated_operator))
(assert
 (= c40cb9fdd_fake_service_bond_wei c40cb9fdd_fake_service_bond_wei))
(assert
 (= c40cb9fdd_instance_locked_indefinitely c40cb9fdd_instance_locked_indefinitely))
(assert
 (= c40cb9fdd_instance_not_yet_registered_flag c40cb9fdd_instance_not_yet_registered_flag))
(assert
 (= c40cb9fdd_legitimate_instance_registered c40cb9fdd_legitimate_instance_registered))
(assert
 (= c40cb9fdd_register_agents_called c40cb9fdd_register_agents_called))
(define-fun report_preconditions () Bool (and c40cb9fdd_bob_owns_instance_flag
     c40cb9fdd_alice_knows_instance_address_flag
     (= 1 c40cb9fdd_fake_service_bond_wei)
     c40cb9fdd_instance_not_yet_registered_flag))
(define-fun report_safety () Bool (=> c40cb9fdd_register_agents_called c40cb9fdd_caller_is_designated_operator))
(define-fun report_effects () Bool (and c40cb9fdd_register_agents_called
     (not c40cb9fdd_caller_is_designated_operator)
     (not c40cb9fdd_legitimate_instance_registered)
     c40cb9fdd_instance_locked_indefinitely
     c40cb9fdd_instance_locked_indefinitely))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
