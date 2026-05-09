package com.abc_bank.abc_bank.security;


import com.abc_bank.abc_bank.auth_users.entity.User;
import com.abc_bank.abc_bank.auth_users.repo.UserRepo;
import com.abc_bank.abc_bank.exceptions.NotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class CustomerUserDetailsService implements UserDetailsService {

    private final UserRepo userRepo ;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        User user=userRepo.findByEmail(username)
                .orElseThrow(()-> new NotFoundException("email not found"));
        return AuthUser.builder()
                .user(user)
                .build();


    }
}
