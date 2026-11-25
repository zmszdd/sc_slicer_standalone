; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1408dc0d_alice_knows_instance_address_flag () Bool)
(declare-fun c1408dc0d_bob_owns_instance_flag () Bool)
(declare-fun c1408dc0d_bob_registration_transaction_fails_flag () Bool)
(declare-fun c1408dc0d_caller_is_designated_operator () Bool)
(declare-fun c1408dc0d_fake_service_bond_wei () Int)
(declare-fun c1408dc0d_instance_registered_elsewhere_flag () Bool)
(declare-fun c1408dc0d_registration_authorized () Bool)
(assert
 (= c1408dc0d_alice_knows_instance_address_flag c1408dc0d_alice_knows_instance_address_flag))
(assert
 (= c1408dc0d_bob_owns_instance_flag c1408dc0d_bob_owns_instance_flag))
(assert
 (= c1408dc0d_bob_registration_transaction_fails_flag c1408dc0d_bob_registration_transaction_fails_flag))
(assert
 (= c1408dc0d_caller_is_designated_operator c1408dc0d_caller_is_designated_operator))
(assert
 (= c1408dc0d_fake_service_bond_wei c1408dc0d_fake_service_bond_wei))
(assert
 (= c1408dc0d_instance_registered_elsewhere_flag c1408dc0d_instance_registered_elsewhere_flag))
(assert
 (= c1408dc0d_registration_authorized c1408dc0d_registration_authorized))
(define-fun report_preconditions () Bool (and c1408dc0d_bob_owns_instance_flag
     c1408dc0d_alice_knows_instance_address_flag
     (<= 1 c1408dc0d_fake_service_bond_wei)
     (not c1408dc0d_instance_registered_elsewhere_flag)))
(define-fun report_safety () Bool (=> c1408dc0d_registration_authorized c1408dc0d_caller_is_designated_operator))
(define-fun report_effects () Bool (and c1408dc0d_registration_authorized
     (not c1408dc0d_caller_is_designated_operator)
     c1408dc0d_bob_registration_transaction_fails_flag
     c1408dc0d_bob_registration_transaction_fails_flag))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
