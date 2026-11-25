; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd96ceac6_alice_knows_instance_address_flag () Bool)
(declare-fun cd96ceac6_bob_owns_instance_flag () Bool)
(declare-fun cd96ceac6_caller_is_designated_operator () Bool)
(declare-fun cd96ceac6_fake_service_bond_wei () Int)
(declare-fun cd96ceac6_instance_funds_lost () Bool)
(declare-fun cd96ceac6_instance_not_yet_registered_flag () Bool)
(declare-fun cd96ceac6_register_agents_effect () Bool)
(assert
 (= cd96ceac6_alice_knows_instance_address_flag cd96ceac6_alice_knows_instance_address_flag))
(assert
 (= cd96ceac6_bob_owns_instance_flag cd96ceac6_bob_owns_instance_flag))
(assert
 (= cd96ceac6_caller_is_designated_operator cd96ceac6_caller_is_designated_operator))
(assert
 (= cd96ceac6_fake_service_bond_wei cd96ceac6_fake_service_bond_wei))
(assert
 (= cd96ceac6_instance_funds_lost cd96ceac6_instance_funds_lost))
(assert
 (= cd96ceac6_instance_not_yet_registered_flag cd96ceac6_instance_not_yet_registered_flag))
(assert
 (= cd96ceac6_register_agents_effect cd96ceac6_register_agents_effect))
(define-fun report_preconditions () Bool (and cd96ceac6_bob_owns_instance_flag
     cd96ceac6_alice_knows_instance_address_flag
     (= 1 cd96ceac6_fake_service_bond_wei)
     cd96ceac6_instance_not_yet_registered_flag))
(define-fun report_safety () Bool (=> cd96ceac6_register_agents_effect cd96ceac6_caller_is_designated_operator))
(define-fun report_effects () Bool (and cd96ceac6_register_agents_effect
     (not cd96ceac6_caller_is_designated_operator)
     cd96ceac6_instance_funds_lost))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
