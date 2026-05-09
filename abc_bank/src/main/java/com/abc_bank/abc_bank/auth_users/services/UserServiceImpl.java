package com.abc_bank.abc_bank.auth_users.services;

import com.abc_bank.abc_bank.auth_users.dtos.LoginRequest;
import com.abc_bank.abc_bank.auth_users.dtos.LoginResponse;
import com.abc_bank.abc_bank.auth_users.dtos.RegistrationRequest;
import com.abc_bank.abc_bank.auth_users.dtos.ResetPasswordRequest;
import com.abc_bank.abc_bank.auth_users.dtos.UpdatePasswordRequest;
import com.abc_bank.abc_bank.auth_users.dtos.UserDTO;
import com.abc_bank.abc_bank.auth_users.entity.PasswordResetCode;
import com.abc_bank.abc_bank.auth_users.entity.User;
import com.abc_bank.abc_bank.auth_users.repo.PasswordResetCodeRepo;
import com.abc_bank.abc_bank.auth_users.repo.UserRepo;
import com.abc_bank.abc_bank.enums.NotificationType;
import com.abc_bank.abc_bank.exceptions.BadRequestException;
import com.abc_bank.abc_bank.exceptions.NotFoundException;
import com.abc_bank.abc_bank.notification.dtos.NotificationDTO;
import com.abc_bank.abc_bank.notification.services.NotificationService;
import com.abc_bank.abc_bank.res.Response;
import com.abc_bank.abc_bank.role.entity.Role;
import com.abc_bank.abc_bank.role.repo.RoleRepo;
import com.abc_bank.abc_bank.security.TokenService;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.modelmapper.ModelMapper;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@Slf4j
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private static final String DEFAULT_ROLE = "ROLE_CUSTOMER";
    private static final long RESET_CODE_TTL_MINUTES = 30;

    private final UserRepo userRepo;
    private final RoleRepo roleRepo;
    private final PasswordResetCodeRepo passwordResetCodeRepo;
    private final PasswordEncoder passwordEncoder;
    private final AuthenticationManager authenticationManager;
    private final TokenService tokenService;
    private final NotificationService notificationService;
    private final ModelMapper modelMapper;

    @Override
    @Transactional
    public Response<UserDTO> registerUser(RegistrationRequest request) {
        if (userRepo.findByEmail(request.getEmail()).isPresent()) {
            throw new BadRequestException("a user with this email already exists");
        }

        List<Role> roles = resolveRoles(request.getRoles());

        User user = User.builder()
                .firstName(request.getFirstName())
                .lastName(request.getLastName())
                .email(request.getEmail())
                .password(passwordEncoder.encode(request.getPassword()))
                .roles(roles)
                .accounts(new ArrayList<>())
                .active(true)
                .createdAt(LocalDateTime.now())
                .build();

        User saved = userRepo.save(user);

        return Response.<UserDTO>builder()
                .statusCode(HttpStatus.CREATED.value())
                .message("user registered successfully")
                .data(toDto(saved))
                .build();
    }

    @Override
    public Response<LoginResponse> loginUser(LoginRequest request) {
        try {
            authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(request.getEmail(), request.getPassword())
            );
        } catch (BadCredentialsException ex) {
            throw new BadRequestException("invalid email or password");
        }

        User user = userRepo.findByEmail(request.getEmail())
                .orElseThrow(() -> new NotFoundException("user not found"));

        if (!user.isActive()) {
            throw new BadRequestException("account is deactivated");
        }

        String token = tokenService.generateToken(user.getEmail());
        List<String> roleNames = user.getRoles() == null
                ? List.of()
                : user.getRoles().stream().map(Role::getName).collect(Collectors.toList());

        LoginResponse loginResponse = LoginResponse.builder()
                .token(token)
                .roles(roleNames)
                .build();

        return Response.<LoginResponse>builder()
                .statusCode(HttpStatus.OK.value())
                .message("login successful")
                .data(loginResponse)
                .build();
    }

    @Override
    public Response<UserDTO> getCurrentUser() {
        User user = getCurrentUserEntity();
        return Response.<UserDTO>builder()
                .statusCode(HttpStatus.OK.value())
                .message("current user fetched")
                .data(toDto(user))
                .build();
    }

    @Override
    public Response<UserDTO> getUserById(Long id) {
        User user = userRepo.findById(id)
                .orElseThrow(() -> new NotFoundException("user not found"));
        return Response.<UserDTO>builder()
                .statusCode(HttpStatus.OK.value())
                .message("user fetched")
                .data(toDto(user))
                .build();
    }

    @Override
    @Transactional
    public Response<?> updatePassword(UpdatePasswordRequest request) {
        User user = getCurrentUserEntity();

        if (!passwordEncoder.matches(request.getOldPassword(), user.getPassword())) {
            throw new BadRequestException("old password is incorrect");
        }

        user.setPassword(passwordEncoder.encode(request.getNewPassword()));
        user.setUpdatedAt(LocalDateTime.now());
        userRepo.save(user);

        return Response.builder()
                .statusCode(HttpStatus.OK.value())
                .message("password updated successfully")
                .build();
    }

    @Override
    @Transactional
    public Response<?> requestPasswordReset(String email) {
        User user = userRepo.findByEmail(email)
                .orElseThrow(() -> new NotFoundException("user not found"));

        passwordResetCodeRepo.deleteByUserId(user.getId());

        String code = UUID.randomUUID().toString();
        PasswordResetCode entry = PasswordResetCode.builder()
                .code(code)
                .user(user)
                .expiryDate(LocalDateTime.now().plusMinutes(RESET_CODE_TTL_MINUTES))
                .used(false)
                .build();
        passwordResetCodeRepo.save(entry);

        NotificationDTO notification = NotificationDTO.builder()
                .recipient(user.getEmail())
                .subject("Password reset code")
                .body("Your password reset code is: " + code
                        + ". It expires in " + RESET_CODE_TTL_MINUTES + " minutes.")
                .type(NotificationType.EMAIL)
                .build();
        notificationService.sendEmail(notification, user);

        return Response.builder()
                .statusCode(HttpStatus.OK.value())
                .message("password reset code sent")
                .build();
    }

    @Override
    @Transactional
    public Response<?> resetPassword(ResetPasswordRequest request) {
        if (request.getCode() == null || request.getNewPassword() == null) {
            throw new BadRequestException("code and newPassword are required");
        }

        PasswordResetCode entry = passwordResetCodeRepo.findByCode(request.getCode())
                .orElseThrow(() -> new BadRequestException("invalid reset code"));

        if (entry.isUsed()) {
            throw new BadRequestException("reset code has already been used");
        }
        if (entry.getExpiryDate() == null || entry.getExpiryDate().isBefore(LocalDateTime.now())) {
            throw new BadRequestException("reset code has expired");
        }

        User user = entry.getUser();
        if (request.getEmail() != null && !request.getEmail().equalsIgnoreCase(user.getEmail())) {
            throw new BadRequestException("reset code does not match the provided email");
        }

        user.setPassword(passwordEncoder.encode(request.getNewPassword()));
        user.setUpdatedAt(LocalDateTime.now());
        userRepo.save(user);

        entry.setUsed(true);
        passwordResetCodeRepo.save(entry);

        return Response.builder()
                .statusCode(HttpStatus.OK.value())
                .message("password reset successful")
                .build();
    }

    @Override
    public User getCurrentUserEntity() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()) {
            throw new BadRequestException("no authenticated user in context");
        }
        String email = authentication.getName();
        return userRepo.findByEmail(email)
                .orElseThrow(() -> new NotFoundException("authenticated user not found"));
    }

    private List<Role> resolveRoles(List<String> requestedRoleNames) {
        List<String> names = (requestedRoleNames == null || requestedRoleNames.isEmpty())
                ? List.of(DEFAULT_ROLE)
                : requestedRoleNames;

        List<Role> roles = new ArrayList<>();
        for (String name : names) {
            Role role = roleRepo.findByName(name)
                    .orElseGet(() -> roleRepo.save(Role.builder().name(name).build()));
            roles.add(role);
        }
        return roles;
    }

    private UserDTO toDto(User user) {
        UserDTO dto = modelMapper.map(user, UserDTO.class);
        dto.setPassword(null);
        return dto;
    }
}
