; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbbbfa767_alice_knows_instance_address_flag () Bool)
(declare-fun cbbbfa767_bob_blocked_from_using_instance () Bool)
(declare-fun cbbbfa767_bob_owns_instance_flag () Bool)
(declare-fun cbbbfa767_caller_is_designated_operator () Bool)
(declare-fun cbbbfa767_fake_service_bond_wei () Int)
(declare-fun cbbbfa767_instance_not_yet_registered_flag () Bool)
(declare-fun cbbbfa767_register_agents_effect () Bool)
(assert
 (= cbbbfa767_alice_knows_instance_address_flag cbbbfa767_alice_knows_instance_address_flag))
(assert
 (= cbbbfa767_bob_blocked_from_using_instance cbbbfa767_bob_blocked_from_using_instance))
(assert
 (= cbbbfa767_bob_owns_instance_flag cbbbfa767_bob_owns_instance_flag))
(assert
 (= cbbbfa767_caller_is_designated_operator cbbbfa767_caller_is_designated_operator))
(assert
 (= cbbbfa767_fake_service_bond_wei cbbbfa767_fake_service_bond_wei))
(assert
 (= cbbbfa767_instance_not_yet_registered_flag cbbbfa767_instance_not_yet_registered_flag))
(assert
 (= cbbbfa767_register_agents_effect cbbbfa767_register_agents_effect))
(define-fun report_preconditions () Bool (and cbbbfa767_bob_owns_instance_flag
     cbbbfa767_alice_knows_instance_address_flag
     (= 1 cbbbfa767_fake_service_bond_wei)
     cbbbfa767_instance_not_yet_registered_flag))
(define-fun report_safety () Bool (=> cbbbfa767_register_agents_effect cbbbfa767_caller_is_designated_operator))
(define-fun report_effects () Bool (and cbbbfa767_register_agents_effect
     (not cbbbfa767_caller_is_designated_operator)
     cbbbfa767_bob_blocked_from_using_instance
     cbbbfa767_bob_blocked_from_using_instance))
