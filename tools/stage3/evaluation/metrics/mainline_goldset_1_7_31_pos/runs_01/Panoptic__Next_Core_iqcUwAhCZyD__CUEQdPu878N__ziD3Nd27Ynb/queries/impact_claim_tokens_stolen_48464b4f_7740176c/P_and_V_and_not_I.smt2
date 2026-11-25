; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2533c029_init_called_by_unauthorized () Bool)
(declare-fun c2533c029_init_completed () Bool)
(declare-fun c2533c029_owner_call_mempool_visible () Bool)
(declare-fun c2533c029_owner_initiated_deployment () Bool)
(declare-fun c2533c029_tokens_stolen_occurred () Bool)
(declare-fun c2533c029_wallet_address_predictable () Bool)
(assert
 (= c2533c029_init_called_by_unauthorized c2533c029_init_called_by_unauthorized))
(assert
 (= c2533c029_init_completed c2533c029_init_completed))
(assert
 (= c2533c029_owner_call_mempool_visible c2533c029_owner_call_mempool_visible))
(assert
 (= c2533c029_owner_initiated_deployment c2533c029_owner_initiated_deployment))
(assert
 (= c2533c029_tokens_stolen_occurred c2533c029_tokens_stolen_occurred))
(assert
 (= c2533c029_wallet_address_predictable c2533c029_wallet_address_predictable))
(define-fun report_preconditions () Bool (and c2533c029_owner_initiated_deployment
     c2533c029_owner_call_mempool_visible
     c2533c029_wallet_address_predictable))
(define-fun report_safety () Bool (=> c2533c029_init_completed (not c2533c029_init_called_by_unauthorized)))
(define-fun report_effects () Bool (and c2533c029_init_completed
     c2533c029_init_called_by_unauthorized
     c2533c029_tokens_stolen_occurred
     c2533c029_tokens_stolen_occurred))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
