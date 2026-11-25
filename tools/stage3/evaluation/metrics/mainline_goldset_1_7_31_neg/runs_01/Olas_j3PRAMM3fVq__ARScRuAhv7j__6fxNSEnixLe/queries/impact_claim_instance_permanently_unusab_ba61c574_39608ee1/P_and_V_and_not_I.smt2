; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdd459fbb_alice_knows_instance_address_flag () Bool)
(declare-fun cdd459fbb_bob_owns_instance_flag () Bool)
(declare-fun cdd459fbb_caller_is_designated_operator () Bool)
(declare-fun cdd459fbb_fake_service_bond_wei () Int)
(declare-fun cdd459fbb_instance_holds_funds_and_nonupgradeable () Bool)
(declare-fun cdd459fbb_instance_not_yet_registered_flag () Bool)
(declare-fun cdd459fbb_instance_permanently_unusable_flag () Bool)
(declare-fun cdd459fbb_instance_registered_to_malicious_service () Bool)
(declare-fun cdd459fbb_register_agents_effect () Bool)
(assert
 (= cdd459fbb_alice_knows_instance_address_flag cdd459fbb_alice_knows_instance_address_flag))
(assert
 (= cdd459fbb_bob_owns_instance_flag cdd459fbb_bob_owns_instance_flag))
(assert
 (= cdd459fbb_caller_is_designated_operator cdd459fbb_caller_is_designated_operator))
(assert
 (= cdd459fbb_fake_service_bond_wei cdd459fbb_fake_service_bond_wei))
(assert
 (= cdd459fbb_instance_holds_funds_and_nonupgradeable cdd459fbb_instance_holds_funds_and_nonupgradeable))
(assert
 (= cdd459fbb_instance_not_yet_registered_flag cdd459fbb_instance_not_yet_registered_flag))
(assert
 (= cdd459fbb_instance_permanently_unusable_flag cdd459fbb_instance_permanently_unusable_flag))
(assert
 (= cdd459fbb_instance_registered_to_malicious_service cdd459fbb_instance_registered_to_malicious_service))
(assert
 (= cdd459fbb_register_agents_effect cdd459fbb_register_agents_effect))
(define-fun report_preconditions () Bool (and cdd459fbb_bob_owns_instance_flag
     cdd459fbb_alice_knows_instance_address_flag
     (= 1 cdd459fbb_fake_service_bond_wei)
     cdd459fbb_instance_not_yet_registered_flag))
(define-fun report_safety () Bool (=> cdd459fbb_register_agents_effect cdd459fbb_caller_is_designated_operator))
(define-fun report_effects () Bool (and cdd459fbb_register_agents_effect
     (not cdd459fbb_caller_is_designated_operator)
     cdd459fbb_instance_registered_to_malicious_service
     cdd459fbb_instance_holds_funds_and_nonupgradeable
     cdd459fbb_instance_permanently_unusable_flag
     cdd459fbb_instance_permanently_unusable_flag))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
